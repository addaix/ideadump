"""Where ideas live: a ``MutableMapping`` of ``/``-separated path to text.

Every verb takes a ``files`` store, so the default local folder can be swapped for any
other ``dol`` store (or a plain ``dict`` in tests) without touching the rest. The
default is a folder, the data root:

1. the ``data_dir`` argument, else
2. ``$IDEADUMP_DATA_DIR``, else
3. ``~/.local/share/ideadump`` (``$XDG_DATA_HOME`` and ``%LOCALAPPDATA%`` honoured).

To keep ideas in a private git repository, make the data root a checkout of it with
``ideadump sync-init <owner>/<name>`` (see :mod:`ideadump.sync`); the store
itself does not change.

>>> data_dir("somewhere").is_absolute()
True
"""

from __future__ import annotations

import os
import time
from collections.abc import Iterator, MutableMapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ideadump.base import APP_NAME, DATA_DIR_ENVVAR, IdeadumpError

__all__ = ["data_dir", "text_files", "resolve_files", "writing"]


def data_dir(data_dir: str | os.PathLike | None = None) -> Path:
    """The data root: the argument, else ``$IDEADUMP_DATA_DIR``, else the user data folder."""
    if data_dir:
        return Path(os.path.abspath(os.path.expanduser(str(data_dir))))
    configured = os.environ.get(DATA_DIR_ENVVAR)
    if configured:
        path = Path(os.path.expanduser(configured))
        if not path.is_absolute():
            raise IdeadumpError(
                f"${DATA_DIR_ENVVAR} must be an absolute path, got {configured!r}"
            )
        return path
    if os.name == "nt":  # pragma: no cover - exercised on Windows CI only
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / APP_NAME
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / APP_NAME


def text_files(root: str | os.PathLike) -> MutableMapping[str, str]:
    """A ``dol`` files store under ``root``: ``/``-separated keys, UTF-8 text values.

    Folders are made on write and never on read; a delete is permanent.
    """
    from dol import Files, mk_dirs_if_missing, wrap_kvs

    root = str(root)
    os.makedirs(root, exist_ok=True)
    files = mk_dirs_if_missing(Files(root, delete_func=os.remove))
    return wrap_kvs(
        files,
        key_of_id=lambda k: k.replace(os.sep, "/"),
        id_of_key=lambda k: k.replace("/", os.sep),
        obj_of_data=lambda b: b.decode("utf-8", errors="replace"),
        data_of_obj=lambda s: s.encode("utf-8"),
    )


def resolve_files(
    files: MutableMapping[str, str] | None = None, *, data_dir_: Any = None
) -> MutableMapping[str, str]:
    """``files`` if given, else the text store over the data root."""
    return text_files(data_dir(data_dir_)) if files is None else files


_LOCK_FILE = ".ideadump.lock"
_LOCK_TIMEOUT = 30.0  # seconds to wait for another writer
_LOCK_STALE = 120.0  # a lock older than this was left by a crashed process
_LOCK_POLL = 0.05


ALLOW_WORK_TREE_ENVVAR = "IDEADUMP_ALLOW_INSIDE_WORK_TREE"


def enclosing_work_tree(root: Path) -> Path | None:
    """The git work tree ``root`` sits inside, when it is not a checkout of its own."""
    if (root / ".git").exists():
        return None
    return next((p for p in root.parents if (p / ".git").exists()), None)


def _refuse_foreign_work_tree(root: Path) -> None:
    enclosing = enclosing_work_tree(root)
    if enclosing and not os.environ.get(ALLOW_WORK_TREE_ENVVAR):
        raise IdeadumpError(
            f"the data folder {root} is inside the git work tree {enclosing}, so a commit "
            "there would carry the ideas. Point $IDEADUMP_DATA_DIR elsewhere, or, if that "
            f"repository is private and meant for them, set ${ALLOW_WORK_TREE_ENVVAR}=1"
        )


@contextmanager
def writing(
    files: MutableMapping[str, str] | None = None,
    *,
    data_dir_: Any = None,
    timeout: float = _LOCK_TIMEOUT,
) -> Iterator[MutableMapping[str, str]]:
    """The store, held exclusively while a verb reads, changes and rewrites it.

    Several sessions may capture ideas at the same moment; each write verb reads every
    record, picks a free id, and rewrites the index, so two of them interleaving would
    lose an idea. For the default folder store this takes a lock file in the data root
    (created exclusively, so it works on every platform); a store passed in by the
    caller is the caller's to serialise.
    """
    if files is not None:
        yield files
        return
    root = data_dir(data_dir_)
    _refuse_foreign_work_tree(root)
    root.mkdir(parents=True, exist_ok=True)
    lock = root / _LOCK_FILE
    deadline = time.monotonic() + timeout
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime > _LOCK_STALE:
                    lock.unlink(missing_ok=True)
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() > deadline:
                raise IdeadumpError(
                    f"another ideadump write holds {lock}; if no other ideadump is running, delete that file"
                ) from None
            time.sleep(_LOCK_POLL)
    try:
        yield text_files(root)
    finally:
        lock.unlink(missing_ok=True)

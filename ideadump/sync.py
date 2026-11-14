"""Keep the data root in a private GitHub repository: commit, rebase, push.

The data root (see :mod:`ideadump.store`) can be a plain folder (the default) or a
checkout of a **private** repository, so ideas are versioned and reachable from any
machine. The git work is not reimplemented here: it is ``acquaint``'s guarded sync
(``acquaint.sync``), which creates the repository private, refuses anything that is not
private, and installs a pre-push guard that re-checks the remote and its visibility on
every push. It is an optional dependency: ``pip install ideadump[git]``.

- ``ideadump sync-init <owner>/<name>`` makes the data root a checkout of that
  repository, creating it private if it does not exist. An existing ideas folder is
  adopted; on a second machine, clone the repository into the data root first.
- ``ideadump sync`` commits everything, rebases onto the remote (acquaint's push raises
  on a conflict rather than committing markers), pushes, then regenerates the pages
  from the merged records. The pages carry a merge driver in ``.gitattributes`` that
  never conflicts, since they are rebuilt anyway. When the data root is not a checkout
  it does nothing and says so: local-only is a normal state.
- ``ideadump sync-status`` reports the remote, uncommitted changes, and visibility.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from ideadump.base import IdeadumpError
from ideadump.store import data_dir as _data_dir
from ideadump.store import writing

__all__ = ["sync", "sync_init", "sync_status"]

#: The pages are regenerated from the records, so a conflict in one is never real:
#: git keeps either side and ``sync`` regenerates them after the rebase.
_MERGE_DRIVER = "ideadump-generated"
_ATTRIBUTES = (
    f"README.md merge={_MERGE_DRIVER}",
    f"ideas/*/README.md merge={_MERGE_DRIVER}",
)
_IGNORED = (".ideadump.lock",)
_EXTRA_HINT = (
    "syncing to a git repository needs the `git` extra: pip install 'ideadump[git]'"
)


def _backend():
    try:
        from acquaint import sync as backend
        from acquaint.store import AcquaintError
    except ImportError as error:  # pragma: no cover - depends on the environment
        raise IdeadumpError(_EXTRA_HINT) from error
    return backend, AcquaintError


def _translate(message: str) -> str:
    """acquaint's messages name its own commands; spell them as ideadump's.

    >>> _translate("run `acquaint sync init --repo a/b --existing-only` first")
    'run `ideadump sync-init a/b` first'
    >>> _translate("then run `acquaint sync push`")
    'then run `ideadump sync`'
    """
    message = re.sub(
        r"acquaint sync init(?: --repo)? (\S+?)(?: --existing-only)?(?=`|\s|$)",
        r"ideadump sync-init \1",
        message,
    )
    message = message.replace("acquaint sync init --repo", "ideadump sync-init")
    return message.replace("acquaint sync push", "ideadump sync")


def _call(func_name: str, *args, **kwargs) -> dict:
    backend, backend_error = _backend()
    try:
        return getattr(backend, func_name)(*args, **kwargs)
    except backend_error as error:
        raise IdeadumpError(_translate(str(error))) from error


def _append_lines(path: Path, lines: tuple[str, ...]) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    missing = [line for line in lines if line not in existing.splitlines()]
    if missing:
        prefix = "" if not existing or existing.endswith("\n") else "\n"
        path.write_text(existing + prefix + "\n".join(missing) + "\n", encoding="utf-8")


def _prepare(root: Path) -> None:
    """Idempotently mark the generated pages as never conflicting, and ignore the lock file."""
    _append_lines(root / ".gitattributes", _ATTRIBUTES)
    _append_lines(root / ".gitignore", _IGNORED)
    subprocess.run(
        ["git", "config", f"merge.{_MERGE_DRIVER}.driver", "true"],
        cwd=root,
        check=True,
        capture_output=True,
    )


def _check_records(root: Path) -> None:
    from ideadump.store import text_files
    from ideadump.tools import _records

    _records(text_files(root))  # raises, naming the file, if one does not parse


def sync_init(repo: str, *, dry_run: bool = False, data_dir: Any = None) -> dict:
    """Make the data root a checkout of the private GitHub repository ``repo`` (owner/name).

    Creates the repository, private, when it does not exist; refuses one that is not
    private. An existing ideas folder is adopted (committed and pushed); a folder that
    is already a checkout of a different repository is refused.
    """
    root = _data_dir(data_dir)
    result = _call("init", root, repo, dry_run=dry_run)
    plan = result.get("plan")
    if plan:
        return {**result, "text": "would:\n- " + "\n- ".join(plan)}
    _prepare(root)
    _call("push", root, message="ideadump: generated pages never conflict")
    return {
        **result,
        "text": f"{root} is now a checkout of {repo} (private); `ideadump sync` pushes",
    }


def sync(*, message: str | None = None, data_dir: Any = None) -> dict:
    """Commit every change in the data root, rebase onto the remote, push (no-op when not a git checkout).

    Refuses while any record does not parse. After the rebase the pages are
    regenerated from the merged records and pushed again if they changed.
    """
    root = _data_dir(data_dir)
    if not (root / ".git").exists():
        return {
            "synced": False,
            "text": f"{root} is local only (not a git checkout); `ideadump sync-init <owner>/<name>` sets that up",
        }
    from ideadump.tools import reindex

    with writing(None, data_dir_=root):
        _check_records(root)
        _prepare(root)
        try:
            pushed = _call("push", root, message=message or "ideadump: sync")
        except IdeadumpError as error:
            raise IdeadumpError(
                f"{error}. If a rebase stopped on a conflict, resolve it in {root} "
                "(`git status`; keep the record you want in idea.json), "
                "`git rebase --continue`, then `ideadump sync`"
            ) from error
    reindex(data_dir=root)
    with writing(None, data_dir_=root):
        again = _call("push", root, message="ideadump: regenerate pages")
    changed = pushed.get("changed_files", 0) + again.get("changed_files", 0)
    text = (
        f"synced {changed} changed files with {pushed.get('repo')}"
        if pushed.get("pushed")
        else pushed.get("note", "nothing to push")
    )
    return {"synced": True, "push": pushed, "text": text}


def sync_status(*, data_dir: Any = None) -> dict:
    """Whether the data root is synced, to which repository, and what is uncommitted."""
    root = _data_dir(data_dir)
    if not (root / ".git").exists():
        return {"synced": False, "root": str(root), "text": f"{root}: local only"}
    result = _call("status", root)
    text = "\n".join(f"{k}: {v}" for k, v in result.items() if k != "text")
    return {**result, "text": text}

"""The verbs: plain functions, JSON-able arguments in, JSON-able dicts out.

This module is the single source of truth for what ideadump does; the command line
(``ideadump.__main__``) and the shipped agent skill are views of the list
:data:`TOOLS`. Every verb takes a ``files`` store (see :mod:`ideadump.store`), so

>>> files = {}
>>> r = add("Maybe a tool to dump ideas into, with a bit of research", title="Idea dump",
...         tags="tools, notes", files=files, now="2026-11-14T10:00:00+01:00")
>>> r["id"]
'2026-11-14-idea-dump'
>>> sorted(files)  # doctest: +NORMALIZE_WHITESPACE
['README.md', 'ideas/2026-11-14-idea-dump/README.md', 'ideas/2026-11-14-idea-dump/idea.json']
>>> find("research tool for ideas", files=files)["hits"][0]["id"]
'2026-11-14-idea-dump'

Verbs never print and never exit; each result carries a ``text`` field, the human
rendering, which the command line prints.
"""

from __future__ import annotations

import functools
import inspect
import json
import re
from collections.abc import Callable, Iterable, MutableMapping
from datetime import datetime
from pathlib import Path
from typing import Any

from ideadump.base import (
    DEPTHS,
    IDEAS_DIR,
    README_FILE,
    RECORD_FILE,
    RESEARCH_DIR,
    STATUSES,
    IdeadumpError,
    record_key,
)
from ideadump.render import created_at, idea_page, index_page, research_depth
from ideadump.search import rank
from ideadump.semantic import resolve_scorer
from ideadump.store import data_dir as _data_dir
from ideadump.store import enclosing_work_tree, resolve_files, writing
from ideadump.sync import sync, sync_init, sync_status

__all__ = [
    "add",
    "show",
    "update",
    "note",
    "link",
    "ls",
    "find",
    "reindex",
    "where",
    "TOOLS",
    "without",
]

Files = MutableMapping[str, str]

#: Parameters that exist for code and tests, not for the command line.
HIDDEN_PARAMETERS = ("files", "data_dir", "now")

_TITLE_WORDS = 8
_SLUG_WORDS = 6


# --------------------------------------------------------------------------- helpers


def _now(now: str | None = None) -> str:
    return now or datetime.now().astimezone().isoformat(timespec="seconds")


def _slug(text: str, *, words: int = _SLUG_WORDS) -> str:
    parts = re.findall(r"[a-z0-9]+", text.lower())
    return "-".join(parts[:words]) or "idea"


def _tag_list(tags: str | Iterable[str] | None) -> list[str]:
    if tags is None:
        return []
    if isinstance(tags, str):
        tags = tags.split(",")
    out = []
    for tag in tags:
        tag = _slug(tag.strip(), words=10) if tag.strip() else ""
        if tag and tag not in out:
            out.append(tag)
    return out


def _default_title(text: str) -> str:
    words = text.split()
    title = " ".join(words[:_TITLE_WORDS]).rstrip(".,;:!?")
    return title + ("…" if len(words) > _TITLE_WORDS else "")


def _records(files: Files) -> dict[str, dict]:
    prefix, suffix = f"{IDEAS_DIR}/", f"/{RECORD_FILE}"
    out = {}
    for key in list(files):
        if key.startswith(prefix) and key.endswith(suffix):
            try:
                record = json.loads(files[key])
                out[record["id"]] = record
            except (ValueError, KeyError, TypeError) as error:
                raise IdeadumpError(
                    f"{key} is not a valid idea record ({error}); fix or restore it "
                    "(it is plain JSON; in a git-synced folder, `git log -p` on it shows earlier versions)"
                ) from error
    return out


def _resolve(idea: str, records: dict[str, dict]) -> str:
    """The id ``idea`` names: an exact id, else the one id containing it."""
    if idea in records:
        return idea
    matches = [i for i in records if idea.lower() in i.lower()]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise IdeadumpError(
            f"no idea matches {idea!r}; `ideadump ls` lists them, `ideadump find` searches"
        )
    raise IdeadumpError(
        f"{idea!r} matches {len(matches)} ideas ({', '.join(sorted(matches)[:5])}); give more of the id"
    )


def _save(files: Files, records: dict[str, dict], touched: Iterable[str]) -> None:
    """Write the touched records, their pages, the pages of ideas linked to them, and the index."""
    titles = {i: r["title"] for i, r in records.items()}
    touched = set(touched)
    pages = set(touched)
    for i in touched:
        pages.update(link["id"] for link in records[i].get("links", []))
    for i in touched:
        files[record_key(i)] = (
            json.dumps(records[i], indent=2, ensure_ascii=False) + "\n"
        )
    for i in pages & records.keys():
        files[f"{IDEAS_DIR}/{i}/{README_FILE}"] = idea_page(records[i], titles=titles)
    files[README_FILE] = index_page(records.values())


def _line(record: dict) -> str:
    tags = ",".join(record.get("tags", []))
    research = research_depth(record)
    return (
        f"{record['id']}  [{record.get('status', 'new')}|{research}]  {record['title']}"
        + (f"  #{tags}" if tags else "")
    )


def _searchable(record: dict, files: Files) -> str:
    """The text an idea is matched on; title and tags weigh more by repetition."""
    parts = [record["title"]] * 3 + [" ".join(record.get("tags", []))] * 2
    parts += [record.get("summary", ""), record.get("words", "")]
    for note in record.get("research", []):
        key = f"{IDEAS_DIR}/{record['id']}/{note['file']}"
        parts.append(note.get("title", ""))
        parts.append(files.get(key, ""))
    return "\n".join(parts)


def _read(file: str) -> str:
    try:
        return Path(file).expanduser().read_text(encoding="utf-8")
    except OSError as error:
        raise IdeadumpError(f"cannot read {file}: {error.strerror or error}") from error


def _writes(verb: Callable) -> Callable:
    """Run a write verb with the store held exclusively (see :func:`ideadump.store.writing`)."""

    @functools.wraps(verb)
    def locked(*args, files: Files | None = None, data_dir: Any = None, **kwargs):
        with writing(files, data_dir_=data_dir) as held:
            return verb(*args, files=held, data_dir=data_dir, **kwargs)

    return locked


# --------------------------------------------------------------------------- verbs


@_writes
def add(
    words: str,
    *,
    title: str | None = None,
    summary: str | None = None,
    tags: str | None = None,
    source: str | None = None,
    status: str = "new",
    files: Files | None = None,
    data_dir: Any = None,
    now: str | None = None,
) -> dict:
    """Capture an idea: the owner's words verbatim, plus an optional title, summary and tags.

    ``words`` is kept exactly as given (dictation slips included); put the cleaned-up
    reading in ``summary``. ``tags`` is comma-separated. ``source`` says where it was
    captured (a session name, "phone"). Returns the new id.
    """
    if not words or not words.strip():
        raise IdeadumpError("an idea needs some words")
    if status not in STATUSES:
        raise IdeadumpError(f"status is one of {', '.join(STATUSES)}, got {status!r}")
    files = resolve_files(files, data_dir_=data_dir)
    records = _records(files)
    stamp = _now(now)
    title = (title or "").strip() or _default_title(summary or words)
    base = f"{stamp[:10]}-{_slug(title)}"
    idea_id, n = base, 2
    while idea_id in records:
        idea_id, n = f"{base}-{n}", n + 1
    record = {
        "id": idea_id,
        "title": title,
        "words": words.strip(),
        "summary": (summary or "").strip(),
        "tags": _tag_list(tags),
        "status": status,
        "source": source or "",
        "created": stamp,
        "updated": stamp,
        "research": [],
        "links": [],
    }
    records[idea_id] = record
    _save(files, records, [idea_id])
    return {"id": idea_id, "record": record, "text": f"captured {_line(record)}"}


def show(idea: str, *, files: Files | None = None, data_dir: Any = None) -> dict:
    """One idea: its record, and the text of its page (words, summary, research, links)."""
    files = resolve_files(files, data_dir_=data_dir)
    records = _records(files)
    idea_id = _resolve(idea, records)
    page = files.get(f"{IDEAS_DIR}/{idea_id}/{README_FILE}") or idea_page(
        records[idea_id]
    )
    return {"id": idea_id, "record": records[idea_id], "text": page}


@_writes
def update(
    idea: str,
    *,
    title: str | None = None,
    summary: str | None = None,
    tags: str | None = None,
    add_tags: str | None = None,
    status: str | None = None,
    files: Files | None = None,
    data_dir: Any = None,
    now: str | None = None,
) -> dict:
    """Change an idea's title, summary, status, or tags (``tags`` replaces, ``add_tags`` adds).

    The owner's words are never edited; the id never changes.
    """
    files = resolve_files(files, data_dir_=data_dir)
    records = _records(files)
    idea_id = _resolve(idea, records)
    record = records[idea_id]
    if status is not None:
        if status not in STATUSES:
            raise IdeadumpError(
                f"status is one of {', '.join(STATUSES)}, got {status!r}"
            )
        record["status"] = status
    if title is not None and title.strip():
        record["title"] = title.strip()
    if summary is not None:
        record["summary"] = summary.strip()
    if tags is not None:
        record["tags"] = _tag_list(tags)
    if add_tags is not None:
        record["tags"] = _tag_list(record["tags"] + _tag_list(add_tags))
    record["updated"] = _now(now)
    _save(files, records, [idea_id])
    return {"id": idea_id, "record": record, "text": f"updated {_line(record)}"}


@_writes
def note(
    idea: str,
    *,
    text: str | None = None,
    file: str | None = None,
    depth: str = "light",
    title: str | None = None,
    files: Files | None = None,
    data_dir: Any = None,
    now: str | None = None,
) -> dict:
    """Attach a research note (Markdown) to an idea, from ``text`` or a ``file`` path.

    ``depth`` is ``light`` (the quick pass at capture) or ``deep`` (a full report).
    Notes are never overwritten: a second note the same day gets its own file.
    """
    if depth not in DEPTHS:
        raise IdeadumpError(f"depth is one of {', '.join(DEPTHS)}, got {depth!r}")
    if (text is None) == (file is None):
        raise IdeadumpError("give the note as --text or as --file, one of the two")
    body = text if text is not None else _read(file)
    if not body.strip():
        raise IdeadumpError("the note is empty")
    files = resolve_files(files, data_dir_=data_dir)
    records = _records(files)
    idea_id = _resolve(idea, records)
    record = records[idea_id]
    stamp = _now(now)
    taken = {n["file"] for n in record["research"]}
    name, n = f"{RESEARCH_DIR}/{stamp[:10]}-{depth}.md", 2
    while name in taken:
        name, n = f"{RESEARCH_DIR}/{stamp[:10]}-{depth}-{n}.md", n + 1
    if not title:
        heading = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        title = (
            heading.group(1).strip() if heading else f"{depth.capitalize()} research"
        )
    files[f"{IDEAS_DIR}/{idea_id}/{name}"] = body.rstrip() + "\n"
    record["research"].append(
        {"file": name, "depth": depth, "date": stamp, "title": title}
    )
    record["updated"] = stamp
    _save(files, records, [idea_id])
    return {
        "id": idea_id,
        "note": name,
        "text": f"noted {depth} research on {idea_id}: {name}",
    }


@_writes
def link(
    idea: str,
    other: str,
    *,
    why: str | None = None,
    files: Files | None = None,
    data_dir: Any = None,
    now: str | None = None,
) -> dict:
    """Relate two ideas, both ways, with an optional one-line reason."""
    files = resolve_files(files, data_dir_=data_dir)
    records = _records(files)
    a, b = _resolve(idea, records), _resolve(other, records)
    if a == b:
        raise IdeadumpError("an idea cannot be linked to itself")
    stamp = _now(now)
    for this, that in ((a, b), (b, a)):
        links = [x for x in records[this]["links"] if x["id"] != that]
        links.append({"id": that, "why": (why or "").strip()})
        records[this]["links"] = links
        records[this]["updated"] = stamp
    _save(files, records, [a, b])
    return {"ids": [a, b], "text": f"linked {a} <-> {b}"}


def ls(
    *,
    tag: str | None = None,
    status: str | None = None,
    limit: int = 50,
    files: Files | None = None,
    data_dir: Any = None,
) -> dict:
    """The ideas, newest first, optionally only those with a tag or a status."""
    files = resolve_files(files, data_dir_=data_dir)
    if status and status not in STATUSES:
        raise IdeadumpError(f"status is one of {', '.join(STATUSES)}, got {status!r}")
    wanted_tags = _tag_list(tag)
    if tag and not wanted_tags:
        raise IdeadumpError(f"{tag!r} is not a usable tag (letters and digits)")
    records = sorted(_records(files).values(), key=created_at, reverse=True)
    if wanted_tags:
        records = [r for r in records if wanted_tags[0] in r.get("tags", [])]
    if status:
        records = [r for r in records if r.get("status") == status]
    shown = records[:limit]
    rows = [
        {k: r.get(k) for k in ("id", "title", "status", "tags", "created")}
        for r in shown
    ]
    text = "\n".join(_line(r) for r in shown) or "no ideas yet"
    if len(records) > limit:
        text += f"\n… and {len(records) - limit} more (--limit)"
    return {"ideas": rows, "total": len(records), "text": text}


def find(
    query: str | None = None,
    *,
    file: str | None = None,
    limit: int = 10,
    files: Files | None = None,
    data_dir: Any = None,
    score: Callable | None = None,
    scorer: str | None = None,
) -> dict:
    """Ideas related to a query, best first: a few words, or a page of text in ``file``.

    ``scorer`` picks how ideas are ranked: ``bm25`` (the default: words, no model, no
    network), ``semantic`` (BM25 blended with ``ir`` embeddings; needs the ``semantic``
    extra), ``light`` (the same with a model-free hashing embedder), or a model name.
    The ``IDEADUMP_SCORER`` environment variable sets it for every call; ``score``
    (a Python callable) wins over both.

    For "is anything I've been working on related to my ideas?", put a description of
    recent work (ledgers, issue titles, commit subjects) in a file and pass ``--file``.
    Each hit lists the words it shares with the query, so a weak match is visible.
    """
    parts = [query or ""]
    if file:
        parts.append(_read(file))
    text = "\n".join(parts).strip()
    if not text:
        raise IdeadumpError("give a query, or --file with the text to match")
    files = resolve_files(files, data_dir_=data_dir)
    records = _records(files)
    docs = {i: _searchable(r, files) for i, r in records.items()}
    score = score or resolve_scorer(scorer)
    hits = rank(text, docs, limit=limit, **({"score": score} if score else {}))
    for hit in hits:
        record = records[hit["id"]]
        hit.update(
            title=record["title"],
            status=record.get("status"),
            tags=record.get("tags", []),
        )
    lines = [
        f"{h['score']:>6}  {_line(records[h['id']])}\n        shares: {', '.join(h['terms']) or '(meaning, no shared words)'}"
        for h in hits
    ]
    return {"hits": hits, "text": "\n".join(lines) or "no related ideas"}


@_writes
def reindex(*, files: Files | None = None, data_dir: Any = None) -> dict:
    """Regenerate every idea page and the root index from the records."""
    files = resolve_files(files, data_dir_=data_dir)
    records = _records(files)
    titles = {i: r["title"] for i, r in records.items()}
    for i, r in records.items():
        files[f"{IDEAS_DIR}/{i}/{README_FILE}"] = idea_page(r, titles=titles)
    files[README_FILE] = index_page(records.values())
    return {"count": len(records), "text": f"reindexed {len(records)} ideas"}


def where(*, data_dir: Any = None) -> dict:
    """Where the ideas are stored, and whether that folder is synced to a git repository."""
    root = _data_dir(data_dir)
    synced = (root / ".git").exists()
    enclosing = enclosing_work_tree(root)
    if synced:
        state = "  (git checkout: `ideadump sync` pushes)"
    elif enclosing:
        state = (
            f"  (inside the git work tree {enclosing}: writes are refused unless "
            "$IDEADUMP_ALLOW_INSIDE_WORK_TREE=1; point $IDEADUMP_DATA_DIR elsewhere)"
        )
    else:
        state = "  (local only)"
    return {
        "data_dir": str(root),
        "git": synced,
        "inside_work_tree": str(enclosing) if enclosing and not synced else None,
        "text": f"{root}{state}",
    }


# --------------------------------------------------------------------------- registry


def without(func: Callable, hidden: Iterable[str] = HIDDEN_PARAMETERS) -> Callable:
    """The same verb with ``hidden`` parameters removed from its signature (for the CLI).

    >>> "files" in inspect.signature(without(show)).parameters
    False
    """
    hidden = set(hidden) | {"score"}
    signature = inspect.signature(func)

    @functools.wraps(func)
    def verb(*args, **kwargs):
        return func(*args, **kwargs)

    verb.__signature__ = signature.replace(
        parameters=[p for p in signature.parameters.values() if p.name not in hidden]
    )
    return verb


TOOLS = [
    add,
    show,
    update,
    note,
    link,
    ls,
    find,
    reindex,
    where,
    sync,
    sync_init,
    sync_status,
]

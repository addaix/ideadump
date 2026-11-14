"""ideadump: a place to dump ideas, research them a little, and find them again.

Capture an idea in the owner's own words, attach research notes (a light pass at
capture, a deep one when it looks promising), tag and link ideas, and ask which ideas
relate to a query or to a page describing recent work. Ideas live in a ``dol`` store,
by default a local folder, optionally a checkout of a private git repository.

>>> from ideadump import add, find
>>> files = {}
>>> _ = add("Offline speech to text on the phone", tags="audio", files=files)
>>> find("speech recognition", files=files)["hits"][0]["tags"]
['audio']

The command line (``ideadump --help``) and the agent skill shipped in
``ideadump/data/skills/ideadump`` drive the same verbs.
"""

from ideadump.base import IdeadumpError
from ideadump.store import data_dir, text_files
from ideadump.sync import sync, sync_init, sync_status
from ideadump.tools import (
    TOOLS,
    add,
    find,
    link,
    ls,
    note,
    reindex,
    show,
    update,
    where,
)

__all__ = [
    "IdeadumpError",
    "TOOLS",
    "add",
    "data_dir",
    "find",
    "link",
    "ls",
    "note",
    "reindex",
    "show",
    "sync",
    "sync_init",
    "sync_status",
    "text_files",
    "update",
    "where",
]

"""Errors and constants shared across ideadump.

An idea is one folder in the store, ``ideas/<id>/``, holding its record
(``idea.json``, the single source of truth), a rendered ``README.md`` that a person
reads on GitHub or a phone, and its research notes under ``research/``. Nothing here
depends on any other module.
"""

from __future__ import annotations

APP_NAME = "ideadump"
DATA_DIR_ENVVAR = "IDEADUMP_DATA_DIR"

IDEAS_DIR = "ideas"
RECORD_FILE = "idea.json"
README_FILE = "README.md"
RESEARCH_DIR = "research"

#: Where an idea stands. ``new`` on capture; the owner (or an agent relaying the
#: owner's words) moves it on. ``promising`` is the cue for a deeper research pass.
STATUSES = ("new", "promising", "parked", "pursued", "dropped")

#: How deep a research note went. ``light`` is the pass made at capture (minutes, a
#: few sources); ``deep`` is a full ``do-research``-style report.
DEPTHS = ("light", "deep")


class IdeadumpError(Exception):
    """An error whose message says what to do next."""


def record_key(idea_id: str) -> str:
    """The store key of an idea's record.

    >>> record_key("2026-11-14-an-idea")
    'ideas/2026-11-14-an-idea/idea.json'
    """
    return f"{IDEAS_DIR}/{idea_id}/{RECORD_FILE}"

---
name: ideadump
description: Capture an idea the owner tells you, in their own words, research it a little (more if it looks promising), tag and link it, and find it again later, with the ideadump command. Use whenever the owner shares an idea unrelated to the current task or asks you to keep one ("I have an idea", "idea:", "jot this down", "dump this idea", "note this idea for later", "remind me of this idea"), asks about their ideas ("what ideas do I have about X", "list my ideas", "show the idea about Y", "research that idea deeper", "that one is promising", "park that idea"), or asks whether anything they have been working on relates to their ideas ("is any of my recent work related to my ideas", "anything in my ideas worth doing now"), typically during spare token budget. Ideas are stored in a local folder or a private git repository, never in the current project.
license: MIT
metadata:
  audience: users
---

# ideadump: a place to dump ideas, and find them again

The owner tells you an idea in passing, often in a session that has nothing to do with it, often dictated. Your job: keep it **in their words**, make it findable, give it a first look, and get out of the way. One command captures it; everything else is optional and cheap.

**First, is it for the current task?** An idea about the work in front of you ("I have an idea: do X this way") is an instruction: act on it, do not dump it. Dump only ideas meant for later or for something else, or when the owner says to keep it.

Ideas live in ideadump's data folder (`ideadump where`), never in the project you are working in. If that folder is a checkout of a private repository, `ideadump sync` pushes; otherwise it is local only, which is fine.

## Capture (always)

```bash
ideadump add "<the owner's words, verbatim>" --title "<short title>" --summary "<your clean reading>" --tags "<tag>, <tag>" --source "<this session's name>"
```

- **Words verbatim**, dictation slips included. Never "fix" them in `words`; put your reading in `--summary`, and when you resolved a slip say so there ("'attic system' read as 'agentic system'"). If a slip changes the meaning and you cannot tell, ask one short question.
- **Title**: five words or fewer, the thing itself ("Idea dump tool", not "An idea about ideas").
- **Tags**: two to four, lowercase, reused from existing ones where they fit: `ideadump ls` shows the tags in use. Prefer the domain (`audio`, `fleet`, `writing`) and the kind (`tool`, `essay`, `research-question`, `business`).
- Then `ideadump find "<title and summary>"` (the new idea is among the hits; ignore its own id): if an earlier idea is the same or close, `ideadump link <id> <other> --why "<one line>"` (or tell the owner it is a duplicate and ask whether to merge).
- Reply to the owner in two lines at most: the id and title, and that a light look follows (or what it found).

**In a session that must keep its context small** (a lookout or switchboard session, or the middle of an unrelated task): run the `add` yourself, then hand the light research to a subagent with the id and these instructions, and carry on with what you were doing.

## Light research (at capture, a few minutes)

Search with the field's generic terms, not the owner's sentences: their words stay in the store, and outside search services see only queries.

Answer four questions, with sources, in a short Markdown note:

1. **What is this called?** The standard name for the idea or its field, if there is one.
2. **What exists already?** Prior art: tools, libraries, papers, products; one line each with a link. If you can search the owner's own packages and skills (in their fleet: `ir discover packages "<two phrasings>"`, `ir discover skills ...`), say what they already have.
3. **What is the crux?** The one thing that would make it hard, or the one thing that makes it easy.
4. **Verdict**: `promising`, `worth a deeper look`, `exists already (use X)`, or `park`, with one sentence of why.

References Vancouver style (`[1]`, `[2]` with a REFERENCES list, `[name](url)` links). Then:

```bash
ideadump note <id> --file <note.md> --depth light
ideadump update <id> --status promising     # only if the verdict says so; parked/dropped likewise
ideadump sync
```

Write the note in a temporary folder, not in the current project.

## Deep research (on request, or when the owner agrees an idea is promising)

Load the `do-research` skill and run it on the idea at deep depth (its report shape, its Vancouver references). Store the report with `ideadump note <id> --file <report.md> --depth deep`, then `ideadump sync`. The report is as private as the idea. If the owner reads on a phone, give them a link only to a destination that is private and access-controlled (in their fleet, `annals publish`, whose links are private; or the idea's page in the private data repository). Never publish it anywhere public.

## Finding ideas

```bash
ideadump ls                                 # newest first; --tag, --status, --limit
ideadump show <id or part of it>            # the idea's page: words, summary, research, links
ideadump find "offline speech recognition"  # ranked, with the words each hit shares with the query
```

The data folder is browsable as it is: `README.md` at its root is the index (newest first, then by tag), and each `ideas/<id>/README.md` is an idea's page, so on GitHub the owner can read it from a phone.

## "Is anything I have been working on related to my ideas?"

1. Gather a page of text describing recent work into a temporary file: what the owner's sessions did lately (in their fleet: `crowsnest ledger` for the per-session ledgers, `ol` for open loops), recent issue and PR titles, recent commit subjects (`git log --since=7.days --format=%s` in the active repositories). A few hundred lines is fine.
2. `ideadump find --file <that file> --limit 15`.
3. The ranking is lexical, so **judge it**: read the top hits' pages (`ideadump show`), keep only those that really relate, and tell the owner, for each, which idea, which work, and the one thing the work could do for the idea (or the idea for the work). Say plainly when nothing relates.
4. Record a real connection: `ideadump update <id> --add-tags <project>` or a line in a research note.

## Other verbs

`ideadump update <id> --title/--summary/--tags/--add-tags/--status`, `ideadump link <a> <b> --why ...`, `ideadump reindex` (regenerate the pages), `ideadump sync-status`, `ideadump sync-init <owner>/<name>` (make the data folder a checkout of a private repository, created private if missing; an existing ideas folder is adopted). `--json` as the last argument of any verb prints the full result. Statuses: `new`, `promising`, `parked`, `pursued`, `dropped`.

## Never

- Never edit `words`; never delete an idea or a note the owner did not ask you to delete.
- Never put idea text in the current project, an issue, or anywhere public. If ideadump refuses because the data folder is inside another git work tree, tell the owner; never set `IDEADUMP_ALLOW_INSIDE_WORK_TREE` yourself.
- Never run deep research unasked on every idea: a light look at capture, deeper only on request or agreement.

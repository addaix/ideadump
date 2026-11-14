# ideadump.tools

The verbs: plain functions, JSON-able arguments in, JSON-able dicts out.

This module is the single source of truth for what ideadump does; the command line
(`ideadump.__main__`) and the shipped agent skill are views of the list
`TOOLS`. Every verb takes a `files` store (see [`ideadump.store`](ideadump.store.html.md#module-ideadump.store)), so

```pycon
>>> files = {}
>>> r = add("Maybe a tool to dump ideas into, with a bit of research", title="Idea dump",
...         tags="tools, notes", files=files, now="2026-11-14T10:00:00+01:00")
>>> r["id"]
'2026-11-14-idea-dump'
>>> sorted(files)
['README.md', 'ideas/2026-11-14-idea-dump/README.md', 'ideas/2026-11-14-idea-dump/idea.json']
>>> find("research tool for ideas", files=files)["hits"][0]["id"]
'2026-11-14-idea-dump'
```

Verbs never print and never exit; each result carries a `text` field, the human
rendering, which the command line prints.

### Functions

| [`add`](#ideadump.tools.add)(words, \*[, title, summary, tags, ...])        | Capture an idea: the owner's words verbatim, plus an optional title, summary and tags.   |
|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| [`show`](#ideadump.tools.show)(idea, \*[, files, data_dir])                  | One idea: its record, and the text of its page (words, summary, research, links).        |
| [`update`](#ideadump.tools.update)(idea, \*[, title, summary, tags, ...])      | Change an idea's title, summary, status, or tags (`tags` replaces, `add_tags` adds).     |
| [`note`](#ideadump.tools.note)(idea, \*[, text, file, depth, title, ...])    | Attach a research note (Markdown) to an idea, from `text` or a `file` path.              |
| [`link`](#ideadump.tools.link)(idea, other, \*[, why, files, data_dir, now]) | Relate two ideas, both ways, with an optional one-line reason.                           |
| [`ls`](#ideadump.tools.ls)(\*[, tag, status, limit, files, data_dir])      | The ideas, newest first, optionally only those with a tag or a status.                   |
| [`find`](#ideadump.tools.find)([query, file, limit, files, data_dir, ...])   | Ideas related to a query, best first: a few words, or a page of text in `file`.          |
| [`reindex`](#ideadump.tools.reindex)(\*[, files, data_dir])                     | Regenerate every idea page and the root index from the records.                          |
| [`where`](#ideadump.tools.where)(\*[, data_dir])                              | Where the ideas are stored, and whether that folder is synced to a git repository.       |
| [`without`](#ideadump.tools.without)(func[, hidden])                            | The same verb with `hidden` parameters removed from its signature (for the CLI).         |

### ideadump.tools.add(words, , title=None, summary=None, tags=None, source=None, status='new', files=None, data_dir=None, now=None)

Capture an idea: the owner’s words verbatim, plus an optional title, summary and tags.

`words` is kept exactly as given (dictation slips included); put the cleaned-up
reading in `summary`. `tags` is comma-separated. `source` says where it was
captured (a session name, “phone”). Returns the new id.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ideadump.tools.find(query=None, , file=None, limit=10, files=None, data_dir=None, score=None)

Ideas related to a query, best first: a few words, or a page of text in `file`.

For “is anything I’ve been working on related to my ideas?”, put a description of
recent work (ledgers, issue titles, commit subjects) in a file and pass `--file`.
Each hit lists the words it shares with the query, so a weak match is visible.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ideadump.tools.link(idea, other, , why=None, files=None, data_dir=None, now=None)

Relate two ideas, both ways, with an optional one-line reason.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ideadump.tools.ls(, tag=None, status=None, limit=50, files=None, data_dir=None)

The ideas, newest first, optionally only those with a tag or a status.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ideadump.tools.note(idea, , text=None, file=None, depth='light', title=None, files=None, data_dir=None, now=None)

Attach a research note (Markdown) to an idea, from `text` or a `file` path.

`depth` is `light` (the quick pass at capture) or `deep` (a full report).
Notes are never overwritten: a second note the same day gets its own file.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ideadump.tools.reindex(, files=None, data_dir=None)

Regenerate every idea page and the root index from the records.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ideadump.tools.show(idea, , files=None, data_dir=None)

One idea: its record, and the text of its page (words, summary, research, links).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ideadump.tools.update(idea, , title=None, summary=None, tags=None, add_tags=None, status=None, files=None, data_dir=None, now=None)

Change an idea’s title, summary, status, or tags (`tags` replaces, `add_tags` adds).

The owner’s words are never edited; the id never changes.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ideadump.tools.where(, data_dir=None)

Where the ideas are stored, and whether that folder is synced to a git repository.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ideadump.tools.without(func, hidden=('files', 'data_dir', 'now'))

The same verb with `hidden` parameters removed from its signature (for the CLI).

```pycon
>>> "files" in inspect.signature(without(show)).parameters
False
```

* **Return type:**
  [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)

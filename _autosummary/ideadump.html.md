# ideadump

ideadump: a place to dump ideas, research them a little, and find them again.

Capture an idea in the owner’s own words, attach research notes (a light pass at
capture, a deep one when it looks promising), tag and link ideas, and ask which ideas
relate to a query or to a page describing recent work. Ideas live in a `dol` store,
by default a local folder, optionally a checkout of a private git repository.

```pycon
>>> from ideadump import add, find
>>> files = {}
>>> _ = add("Offline speech to text on the phone", tags="audio", files=files)
>>> find("speech recognition", files=files)["hits"][0]["tags"]
['audio']
```

The command line (`ideadump --help`) and the agent skill shipped in
`ideadump/data/skills/ideadump` drive the same verbs.

### Functions

| [`add`](#ideadump.add)(words, \*[, title, summary, tags, ...])        | Capture an idea: the owner's words verbatim, plus an optional title, summary and tags.              |
|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| [`data_dir`](#ideadump.data_dir)([data_dir])                               | The data root: the argument, else `$IDEADUMP_DATA_DIR`, else the user data folder.                  |
| [`find`](#ideadump.find)([query, file, limit, files, data_dir, ...])   | Ideas related to a query, best first: a few words, or a page of text in `file`.                     |
| [`link`](#ideadump.link)(idea, other, \*[, why, files, data_dir, now]) | Relate two ideas, both ways, with an optional one-line reason.                                      |
| [`ls`](#ideadump.ls)(\*[, tag, status, limit, files, data_dir])      | The ideas, newest first, optionally only those with a tag or a status.                              |
| [`note`](#ideadump.note)(idea, \*[, text, file, depth, title, ...])    | Attach a research note (Markdown) to an idea, from `text` or a `file` path.                         |
| [`reindex`](#ideadump.reindex)(\*[, files, data_dir])                     | Regenerate every idea page and the root index from the records.                                     |
| [`show`](#ideadump.show)(idea, \*[, files, data_dir])                  | One idea: its record, and the text of its page (words, summary, research, links).                   |
| [`sync`](#ideadump.sync)(\*[, message, data_dir])                      | Commit every change in the data root, rebase onto the remote, push (no-op when not a git checkout). |
| [`sync_init`](#ideadump.sync_init)(repo, \*[, dry_run, data_dir])           | Make the data root a checkout of the private GitHub repository `repo` (owner/name).                 |
| [`sync_status`](#ideadump.sync_status)(\*[, data_dir])                        | Whether the data root is synced, to which repository, and what is uncommitted.                      |
| [`text_files`](#ideadump.text_files)(root)                                   | A `dol` files store under `root`: `/`-separated keys, UTF-8 text values.                            |
| [`update`](#ideadump.update)(idea, \*[, title, summary, tags, ...])      | Change an idea's title, summary, status, or tags (`tags` replaces, `add_tags` adds).                |
| [`where`](#ideadump.where)(\*[, data_dir])                              | Where the ideas are stored, and whether that folder is synced to a git repository.                  |

### Exceptions

| [`IdeadumpError`](#ideadump.IdeadumpError)   | An error whose message says what to do next.   |
|------------------------------------------------------------------|------------------------------------------------|

### *exception* ideadump.IdeadumpError

Bases: [`Exception`](https://docs.python.org/3/builtins/exceptions.html#Exception)

An error whose message says what to do next.

### ideadump.add(words, , title=None, summary=None, tags=None, source=None, status='new', files=None, data_dir=None, now=None)

Capture an idea: the owner’s words verbatim, plus an optional title, summary and tags.

`words` is kept exactly as given (dictation slips included); put the cleaned-up
reading in `summary`. `tags` is comma-separated. `source` says where it was
captured (a session name, “phone”). Returns the new id.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ideadump.data_dir(data_dir=None)

The data root: the argument, else `$IDEADUMP_DATA_DIR`, else the user data folder.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### ideadump.find(query=None, , file=None, limit=10, files=None, data_dir=None, score=None, scorer=None)

Ideas related to a query, best first: a few words, or a page of text in `file`.

`scorer` picks how ideas are ranked: `bm25` (the default: words, no model, no
network), `semantic` (BM25 blended with `ir` embeddings; needs the `semantic`
extra), `light` (the same with a model-free hashing embedder), or a model name.
The `IDEADUMP_SCORER` environment variable sets it for every call; `score`
(a Python callable) wins over both.

For “is anything I’ve been working on related to my ideas?”, put a description of
recent work (ledgers, issue titles, commit subjects) in a file and pass `--file`.
Each hit lists the words it shares with the query, so a weak match is visible.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ideadump.link(idea, other, , why=None, files=None, data_dir=None, now=None)

Relate two ideas, both ways, with an optional one-line reason.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ideadump.ls(, tag=None, status=None, limit=50, files=None, data_dir=None)

The ideas, newest first, optionally only those with a tag or a status.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ideadump.note(idea, , text=None, file=None, depth='light', title=None, files=None, data_dir=None, now=None)

Attach a research note (Markdown) to an idea, from `text` or a `file` path.

`depth` is `light` (the quick pass at capture) or `deep` (a full report).
Notes are never overwritten: a second note the same day gets its own file.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ideadump.reindex(, files=None, data_dir=None)

Regenerate every idea page and the root index from the records.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ideadump.show(idea, , files=None, data_dir=None)

One idea: its record, and the text of its page (words, summary, research, links).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ideadump.sync(, message=None, data_dir=None)

Commit every change in the data root, rebase onto the remote, push (no-op when not a git checkout).

Refuses while any record does not parse. After the rebase the pages are
regenerated from the merged records and pushed again if they changed.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ideadump.sync_init(repo, , dry_run=False, data_dir=None)

Make the data root a checkout of the private GitHub repository `repo` (owner/name).

Creates the repository, private, when it does not exist; refuses one that is not
private. An existing ideas folder is adopted (committed and pushed); a folder that
is already a checkout of a different repository is refused.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ideadump.sync_status(, data_dir=None)

Whether the data root is synced, to which repository, and what is uncommitted.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ideadump.text_files(root)

A `dol` files store under `root`: `/`-separated keys, UTF-8 text values.

Folders are made on write and never on read; a delete is permanent.

* **Return type:**
  [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### ideadump.update(idea, , title=None, summary=None, tags=None, add_tags=None, status=None, files=None, data_dir=None, now=None)

Change an idea’s title, summary, status, or tags (`tags` replaces, `add_tags` adds).

The owner’s words are never edited; the id never changes.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ideadump.where(, data_dir=None)

Where the ideas are stored, and whether that folder is synced to a git repository.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### Modules

| [`base`](ideadump.base.html.md#module-ideadump.base)         | Errors and constants shared across ideadump.                                                                                                    |
|------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| [`render`](ideadump.render.html.md#module-ideadump.render)     | Markdown views of the records: one `README.md` per idea and an index at the root.                                                               |
| [`search`](ideadump.search.html.md#module-ideadump.search)     | Rank ideas against a query: BM25 over words, standard library only.                                                                             |
| [`semantic`](ideadump.semantic.html.md#module-ideadump.semantic) | A semantic scorer for [`ideadump.search.rank()`](ideadump.search.html.md#ideadump.search.rank), backed by the fleet's `ir`. |
| [`store`](ideadump.store.html.md#module-ideadump.store)       | Where ideas live: a `MutableMapping` of `/`-separated path to text.                                                                             |
| [`tools`](ideadump.tools.html.md#module-ideadump.tools)       | The verbs: plain functions, JSON-able arguments in, JSON-able dicts out.                                                                        |

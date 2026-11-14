# ideadump.render

Markdown views of the records: one `README.md` per idea and an index at the root.

The records (`idea.json`) are the source of truth; these pages are regenerated from
them on every write, so a person browsing the store on GitHub (or a phone) sees each
idea’s folder open on its page, and the root opens on the index.

### Functions

| [`idea_page`](#ideadump.render.idea_page)(record, \*[, titles])   | The page of one idea: the owner's words, the summary, research and links.      |
|------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| [`index_page`](#ideadump.render.index_page)(records)               | The root index: every idea, newest first, then the ideas under each tag.       |
| [`research_depth`](#ideadump.render.research_depth)(record)            | How far an idea has been researched: `deep`, `light` or `-`.                   |
| [`created_at`](#ideadump.render.created_at)(record)                | When an idea was captured, comparable across machines in different time zones. |

### ideadump.render.created_at(record)

When an idea was captured, comparable across machines in different time zones.

```pycon
>>> a = {"created": "2026-11-14T23:30:00+01:00"}
>>> b = {"created": "2026-11-14T22:45:00+00:00"}
>>> created_at(a) < created_at(b)
True
```

* **Return type:**
  [`datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime)

### ideadump.render.idea_page(record, , titles=None)

The page of one idea: the owner’s words, the summary, research and links.

```pycon
>>> page = idea_page({"id": "x", "title": "T", "words": "w", "created": "2026-11-14"})
>>> page.splitlines()[0]
'# T'
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### ideadump.render.index_page(records)

The root index: every idea, newest first, then the ideas under each tag.

```pycon
>>> print(index_page([]).splitlines()[0])
# Ideas
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### ideadump.render.research_depth(record)

How far an idea has been researched: `deep`, `light` or `-`.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

# ideadump: dev map

Seams (each one keyword argument, default first):

| Seam | Default | Replacement you can point at |
|---|---|---|
| `files=` where records live (every record verb; `where`/`sync*` work on the data folder itself) | `dol` text files over `~/.local/share/ideadump` (`$IDEADUMP_DATA_DIR`) | any `MutableMapping` (a `dict` in tests, another `dol` store) |
| `score=` how `find` ranks (`search.rank`, `tools.find`) | BM25, standard library | a semantic scorer over the fleet's `ir` |

Sync is not a seam: `ideadump/sync.py` delegates to `acquaint.sync` (optional extra `git`), whose extraction into its own component is https://github.com/thorwhalen/acquaint/issues/46. Write verbs hold a lock file in the data root (`store.writing`), since several sessions capture at once.

Surfaces built: the shipped skill (`ideadump/data/skills/ideadump/SKILL.md`, symlinked from `.claude/skills/`) and the CLI (`cw.dispatch` over `tools.TOOLS`). MCP: `py2mcp.mk_mcp_from_refs(['ideadump.tools:add', ...])` would need no core change; not built. HTTP/frontend: no consumer.

NOT seams: the id format (`YYYY-MM-DD-slug`), the page and index rendering (`render.py`), the stopword list.

Layout: `base.py` (constants, error) → `store.py` (data root, dol store) → `search.py` (BM25) → `render.py` (pages) → `tools.py` (the verbs, SSOT) → `__main__.py` (CLI). `idea.json` is the source of truth; READMEs are regenerated on every write.

Test: `python -m pytest` (doctests included). The one-command test is `tests/test_smoke.py::test_cli_end_to_end`.

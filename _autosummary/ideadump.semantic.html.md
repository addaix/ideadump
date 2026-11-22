# ideadump.semantic

A semantic scorer for [`ideadump.search.rank()`](ideadump.search.html.md#ideadump.search.rank), backed by the fleet’s `ir`.

BM25 (the default, standard library, no network, no model) misses ideas that share
meaning but not words. [`hybrid_scorer()`](#ideadump.semantic.hybrid_scorer) adds embedding similarity from `ir`’s
embedders, blended with BM25 so an exact word match still counts. It needs the
`semantic` extra (`ir`); with the `"light"` embedder it needs no model download
(a numpy hashing embedder, lexical in spirit), while the default is a local
sentence-transformers model.

```pycon
>>> scorer = hybrid_scorer("light")
>>> scores = scorer("offline speech to text", ["speech to text on a phone", "bread recipe"])
>>> scores[0] > scores[1]
True
```

[`resolve_scorer()`](#ideadump.semantic.resolve_scorer) maps the names a command line or environment variable can carry
(`"bm25"`, `"semantic"`, `"light"`, or any sentence-transformers model name) to a
scorer, so the CLI needs no code of its own.

### Module Attributes

| [`SCORER_ENV_VAR`](#ideadump.semantic.SCORER_ENV_VAR)   | The environment variable that selects the scorer when none is passed.                     |
|-------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| [`SCORER_NAMES`](#ideadump.semantic.SCORER_NAMES)     | Names with a fixed meaning; any other string is taken as an `ir` embedder (a model name). |

### Functions

| [`hybrid_scorer`](#ideadump.semantic.hybrid_scorer)([embedder, weight, cosine_floor])   | A `score(query, docs)` blending BM25 with `ir`-embedding cosine similarity.   |
|----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| [`resolve_scorer`](#ideadump.semantic.resolve_scorer)([name])                            | The scorer for `name`, or `None` for the BM25 default.                        |

### ideadump.semantic.SCORER_ENV_VAR *= 'IDEADUMP_SCORER'*

The environment variable that selects the scorer when none is passed.

### ideadump.semantic.SCORER_NAMES *= ('bm25', 'semantic', 'light')*

Names with a fixed meaning; any other string is taken as an `ir` embedder (a model name).

### ideadump.semantic.hybrid_scorer(embedder='default', , weight=0.5, cosine_floor=0.2)

A `score(query, docs)` blending BM25 with `ir`-embedding cosine similarity.

* **Parameters:**
  * **embedder** – an `ir` embedder spec: `"default"` (local model),
    `"light"` (hashing, no download), or a model name.
  * **weight** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – share of the embedding score in the blend, in `[0, 1]`.
  * **cosine_floor** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – cosine below which a document counts as unrelated.
* **Raises:**
  [**IdeadumpError**](ideadump.html.md#ideadump.IdeadumpError) – if `ir` (the `semantic` extra) is not installed.
* **Return type:**
  [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)[[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Sequence`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]], [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]]

### ideadump.semantic.resolve_scorer(name=None)

The scorer for `name`, or `None` for the BM25 default.

`name` falls back to the [`SCORER_ENV_VAR`](#ideadump.semantic.SCORER_ENV_VAR) environment variable, then to
`"bm25"`. `"semantic"` is the hybrid with `ir`’s default local model,
`"light"` the hybrid with the hashing embedder, and any other string the hybrid
with that embedder (a model name).

* **Return type:**
  [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable) | [`None`](https://docs.python.org/3/builtins/constants.html#None)

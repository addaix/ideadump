# ideadump.search

Rank ideas against a query: BM25 over words, standard library only.

The query can be a few words (“offline speech to text”) or a page of text describing
recent work (ledgers, issue titles, commit messages): long queries are the “is
anything I’ve been working on related to my ideas?” case. The scorer is a seam: any
`score(query, docs) -> list[float]` can be passed to [`rank()`](#ideadump.search.rank), for instance a
semantic scorer backed by the fleet’s `ir` search.

```pycon
>>> docs = {"a": "offline speech to text on a phone", "b": "a recipe for bread"}
>>> [hit["id"] for hit in rank("speech recognition offline", docs)]
['a']
```

### Functions

| [`tokens`](#ideadump.search.tokens)(text)                          | Lowercased content words of `text`, with a light plural fold.                  |
|----------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| [`bm25`](#ideadump.search.bm25)(query, docs, \*[, k1, b])        | BM25 score of each document for `query` (query terms counted once each).       |
| [`rank`](#ideadump.search.rank)(query, docs, \*[, limit, score]) | The ids of `docs` that match `query`, best first, with score and shared terms. |

### ideadump.search.bm25(query, docs, , k1=1.5, b=0.75)

BM25 score of each document for `query` (query terms counted once each).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]

### ideadump.search.rank(query, docs, \*, limit=10, score=<function bm25>)

The ids of `docs` that match `query`, best first, with score and shared terms.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]

### ideadump.search.tokens(text)

Lowercased content words of `text`, with a light plural fold.

```pycon
>>> tokens("The ideas, and an Idea!")
['idea', 'idea']
```

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

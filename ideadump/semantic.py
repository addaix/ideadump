"""A semantic scorer for :func:`ideadump.search.rank`, backed by the fleet's ``ir``.

BM25 (the default, standard library, no network, no model) misses ideas that share
meaning but not words. :func:`hybrid_scorer` adds embedding similarity from ``ir``'s
embedders, blended with BM25 so an exact word match still counts. It needs the
``semantic`` extra (``ir``); with the ``"light"`` embedder it needs no model download
(a numpy hashing embedder, lexical in spirit), while the default is a local
sentence-transformers model.

>>> scorer = hybrid_scorer("light")  # doctest: +SKIP
>>> scores = scorer("offline speech to text", ["speech to text on a phone", "bread recipe"])  # doctest: +SKIP
>>> scores[0] > scores[1]  # doctest: +SKIP
True

:func:`resolve_scorer` maps the names a command line or environment variable can carry
(``"bm25"``, ``"semantic"``, ``"light"``, or any sentence-transformers model name) to a
scorer, so the CLI needs no code of its own.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence

from ideadump.base import IdeadumpError
from ideadump.search import bm25

__all__ = ["hybrid_scorer", "resolve_scorer", "SCORER_ENV_VAR", "SCORER_NAMES"]

#: The environment variable that selects the scorer when none is passed.
SCORER_ENV_VAR = "IDEADUMP_SCORER"
#: Names with a fixed meaning; any other string is taken as an ``ir`` embedder (a model name).
SCORER_NAMES = ("bm25", "semantic", "light")

#: Weight of the embedding score against BM25 in the blend (0 = BM25 only, 1 = embeddings only).
DEFAULT_SEMANTIC_WEIGHT = 0.5
#: Cosine similarity an unrelated pair already has with a sentence model; subtracted so
#: unrelated ideas score zero and drop out of the hits.
DEFAULT_COSINE_FLOOR = 0.2


def hybrid_scorer(
    embedder="default",
    *,
    weight: float = DEFAULT_SEMANTIC_WEIGHT,
    cosine_floor: float = DEFAULT_COSINE_FLOOR,
) -> Callable[[str, Sequence[str]], list[float]]:
    """A ``score(query, docs)`` blending BM25 with ``ir``-embedding cosine similarity.

    :param embedder: an ``ir`` embedder spec: ``"default"`` (local model),
        ``"light"`` (hashing, no download), or a model name.
    :param weight: share of the embedding score in the blend, in ``[0, 1]``.
    :param cosine_floor: cosine below which a document counts as unrelated.
    :raises IdeadumpError: if ``ir`` (the ``semantic`` extra) is not installed.
    """
    if not 0 <= weight <= 1:
        raise ValueError(f"weight must be in [0, 1], got {weight!r}")
    try:
        from ir.embed import make_embedder
    except ImportError as error:
        raise IdeadumpError(
            "the semantic scorer needs ir: install ideadump with its 'semantic' extra"
        ) from error
    embed, _ = make_embedder(embedder)

    def score(query: str, docs: Sequence[str]) -> list[float]:
        docs = list(docs)
        if not docs:
            return []
        lexical = bm25(query, docs)
        top = max(lexical) or 1.0
        vectors = embed([query, *docs])
        query_vector, doc_vectors = vectors[0], vectors[1:]
        norms = (doc_vectors**2).sum(axis=1) ** 0.5 * (query_vector**2).sum() ** 0.5
        cosine = (doc_vectors @ query_vector) / (norms + 1e-12)
        return [
            (1 - weight) * lex / top + weight * max(float(c) - cosine_floor, 0.0)
            for lex, c in zip(lexical, cosine)
        ]

    return score


def resolve_scorer(name: str | None = None) -> Callable | None:
    """The scorer for ``name``, or ``None`` for the BM25 default.

    ``name`` falls back to the :data:`SCORER_ENV_VAR` environment variable, then to
    ``"bm25"``. ``"semantic"`` is the hybrid with ``ir``'s default local model,
    ``"light"`` the hybrid with the hashing embedder, and any other string the hybrid
    with that embedder (a model name).
    """
    name = (name or os.environ.get(SCORER_ENV_VAR) or "bm25").strip()
    key = name.lower()
    if key == "bm25":
        return None
    return hybrid_scorer("default" if key == "semantic" else name)

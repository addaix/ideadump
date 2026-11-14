"""Rank ideas against a query: BM25 over words, standard library only.

The query can be a few words ("offline speech to text") or a page of text describing
recent work (ledgers, issue titles, commit messages): long queries are the "is
anything I've been working on related to my ideas?" case. The scorer is a seam: any
``score(query, docs) -> list[float]`` can be passed to :func:`rank`, for instance a
semantic scorer backed by the fleet's ``ir`` search.

>>> docs = {"a": "offline speech to text on a phone", "b": "a recipe for bread"}
>>> [hit["id"] for hit in rank("speech recognition offline", docs)]
['a']
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Callable, Mapping, Sequence

__all__ = ["tokens", "bm25", "rank"]

_WORD = re.compile(r"[a-z0-9][a-z0-9+#.-]*[a-z0-9+#]|[a-z0-9]", re.IGNORECASE)

# Function words carry no topic; dropping them keeps a page-long query from matching
# every idea on "the" and "with".
_STOPWORDS = frozenset(
    """a about above after again all also am an and any are as at be because been
    before being below between both but by can could did do does doing down during
    each few for from further had has have having he her here hers him his how i if
    in into is it its itself just let like make me more most my no nor not now of off
    on once only or other our out over own same she should so some such than that the
    their them then there these they this those through to too under until up very
    was we were what when where which while who whom why will with would you your
    yours maybe really thing things want wanna gonna get got way use using one also""".split()
)


def tokens(text: str) -> list[str]:
    """Lowercased content words of ``text``, with a light plural fold.

    >>> tokens("The ideas, and an Idea!")
    ['idea', 'idea']
    """
    out = []
    for word in _WORD.findall(text.lower()):
        if word in _STOPWORDS or len(word) < 2:
            continue
        if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]
        out.append(word)
    return out


def bm25(
    query: str, docs: Sequence[str], *, k1: float = 1.5, b: float = 0.75
) -> list[float]:
    """BM25 score of each document for ``query`` (query terms counted once each)."""
    doc_tokens = [tokens(d) for d in docs]
    n = len(doc_tokens)
    if not n:
        return []
    avg_len = sum(map(len, doc_tokens)) / n or 1.0
    df = Counter(t for toks in doc_tokens for t in set(toks))
    terms = set(tokens(query))
    scores = []
    for toks in doc_tokens:
        tf = Counter(toks)
        norm = k1 * (1 - b + b * len(toks) / avg_len)
        score = 0.0
        for t in terms & tf.keys():
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            score += idf * tf[t] * (k1 + 1) / (tf[t] + norm)
        scores.append(score)
    return scores


def rank(
    query: str,
    docs: Mapping[str, str],
    *,
    limit: int = 10,
    score: Callable[[str, Sequence[str]], list[float]] = bm25,
) -> list[dict]:
    """The ids of ``docs`` that match ``query``, best first, with score and shared terms."""
    ids = list(docs)
    scores = score(query, [docs[i] for i in ids])
    query_terms = set(tokens(query))
    hits = [
        {
            "id": i,
            "score": round(s, 3),
            "terms": sorted(query_terms & set(tokens(docs[i])))[:12],
        }
        for i, s in zip(ids, scores)
        if s > 0
    ]
    hits.sort(key=lambda h: -h["score"])
    return hits[:limit]

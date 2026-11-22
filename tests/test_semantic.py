"""The semantic scorer: a seam on `find`, selected by name, with BM25 left as the default."""

import pytest

from ideadump import add, find
from ideadump.base import IdeadumpError
from ideadump.semantic import SCORER_ENV_VAR, hybrid_scorer, resolve_scorer

NOW = "2026-11-14T10:00:00+01:00"


def test_bm25_is_the_default_and_needs_nothing(monkeypatch):
    monkeypatch.delenv(SCORER_ENV_VAR, raising=False)
    assert resolve_scorer(None) is None
    assert resolve_scorer("BM25") is None


def test_the_environment_variable_selects_the_scorer(monkeypatch):
    pytest.importorskip("ir")
    monkeypatch.setenv(SCORER_ENV_VAR, "light")
    assert callable(resolve_scorer(None))
    assert resolve_scorer("bm25") is None  # an explicit name wins over the environment


def test_hybrid_scores_a_related_document_above_an_unrelated_one():
    pytest.importorskip("ir")
    score = hybrid_scorer("light")
    related, unrelated = score(
        "offline speech to text", ["speech to text on a phone, offline", "a recipe for bread"]
    )
    assert related > unrelated >= 0


def test_weight_zero_is_bm25_ordering():
    pytest.importorskip("ir")
    from ideadump.search import bm25

    docs = ["offline speech to text", "bread", "speech"]
    blended = hybrid_scorer("light", weight=0)("speech to text", docs)
    lexical = bm25("speech to text", docs)
    top = max(lexical)
    assert blended == pytest.approx([x / top for x in lexical])


def test_weight_out_of_range_is_refused():
    with pytest.raises(ValueError):
        hybrid_scorer("light", weight=1.5)


def test_find_takes_a_scorer_name(tmp_path):
    pytest.importorskip("ir")
    data = tmp_path / "ideas"
    add("offline speech to text on a phone", data_dir=data, now=NOW)
    add("a recipe for bread", data_dir=data, now=NOW)
    hits = find("speech to text", data_dir=data, scorer="light")["hits"]
    assert hits and "speech" in hits[0]["title"].lower()


def test_missing_ir_says_how_to_install(monkeypatch):
    import builtins

    real = builtins.__import__

    def refuse(name, *a, **k):
        if name == "ir" or name.startswith("ir."):
            raise ImportError(name)
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", refuse)
    with pytest.raises(IdeadumpError, match="semantic"):
        hybrid_scorer("light")

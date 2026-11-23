"""The sync path (with a fake backend) and the ``score=`` seam of ``find`` (addaix/ideadump#7)."""

import subprocess
import types

import pytest

import importlib

from ideadump import add, find

sync_module = importlib.import_module("ideadump.sync")
from ideadump.base import IdeadumpError
from ideadump.sync import _prepare, _translate, sync, sync_status

NOW = "2026-11-14T10:00:00+01:00"


class FakeBackendError(Exception):
    pass


def fake_backend(monkeypatch, *, push=None, status=None):
    calls = []

    def _push(root, *, message):
        calls.append(("push", message))
        if push is not None:
            return push(root, message)
        return {"pushed": True, "changed_files": 1, "repo": "me/ideas"}

    backend = types.SimpleNamespace(
        push=_push,
        status=lambda root: status or {"remote": "me/ideas", "visibility": "private"},
        init=lambda root, repo, dry_run=False: {"plan": ["create"]} if dry_run else {"repo": repo},
    )
    monkeypatch.setattr(sync_module, "_backend", lambda: (backend, FakeBackendError))
    return calls


@pytest.fixture
def checkout(tmp_path):
    root = tmp_path / "ideas"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    add("an idea about sync", title="Sync", data_dir=root, now=NOW)
    return root


def test_sync_is_noop_when_not_a_checkout(tmp_path):
    result = sync(data_dir=tmp_path / "plain")
    assert result["synced"] is False and "local only" in result["text"]


def test_sync_status_local_only(tmp_path):
    assert sync_status(data_dir=tmp_path)["synced"] is False


def test_sync_pushes_twice_and_reports_changes(checkout, monkeypatch):
    calls = fake_backend(monkeypatch)
    result = sync(data_dir=checkout, message="mine")
    assert result["synced"] is True
    assert [c[1] for c in calls] == ["mine", "ideadump: regenerate pages"]
    assert "synced 2 changed files" in result["text"]


def test_sync_prepares_gitattributes_and_gitignore(checkout, monkeypatch):
    fake_backend(monkeypatch)
    sync(data_dir=checkout)
    assert "merge=ideadump-generated" in (checkout / ".gitattributes").read_text()
    assert ".ideadump.lock" in (checkout / ".gitignore").read_text()
    _prepare(checkout)  # idempotent
    assert (checkout / ".gitattributes").read_text().count("README.md merge=") == 2


def test_sync_translates_backend_errors_and_hints_at_conflicts(checkout, monkeypatch):
    def boom(root, message):
        raise FakeBackendError("then run `acquaint sync push`")

    fake_backend(monkeypatch, push=boom)
    with pytest.raises(IdeadumpError) as info:
        sync(data_dir=checkout)
    text = str(info.value)
    assert "ideadump sync" in text and "acquaint" not in text and "git rebase --continue" in text


def test_sync_refuses_unparseable_records(checkout, monkeypatch):
    calls = fake_backend(monkeypatch)
    (checkout / "ideas").mkdir(exist_ok=True)
    bad = next(checkout.rglob("idea.json"))
    bad.write_text("{not json")
    with pytest.raises(Exception):
        sync(data_dir=checkout)
    assert calls == []


def test_translate_init_message():
    assert _translate("run `acquaint sync init --repo a/b --existing-only` first") == (
        "run `ideadump sync-init a/b` first"
    )


def test_find_uses_a_custom_score_callable(tmp_path):
    add("alpha words only", title="A", data_dir=tmp_path, now=NOW)
    add("beta words only", title="B", data_dir=tmp_path, now=NOW)
    seen = {}

    def score(query, docs):
        seen["n"] = len(docs)
        return [1.0 if "beta" in d else 0.0 for d in docs]

    result = find("anything at all", data_dir=tmp_path, score=score)
    assert seen["n"] == 2
    text = result["text"]
    assert "-b " in text and "-a " not in text

"""The one-command test: capture, research, link, find and list, on a real folder, through the CLI."""

import json
import os
import subprocess
import sys

import pytest

from ideadump import add, find, link, ls, note, show, update
from ideadump.base import IdeadumpError
from ideadump.store import text_files

NOW = "2026-11-14T10:00:00+01:00"


def run_cli(*args, data_dir):
    result = subprocess.run(
        [sys.executable, "-m", "ideadump", *args],
        capture_output=True,
        text=True,
        env={**os.environ, "IDEADUMP_DATA_DIR": str(data_dir)},
    )
    return result


def test_cli_end_to_end(tmp_path):
    data = tmp_path / "ideas"
    r = run_cli(
        "add",
        "I want a place to dump ideas and do a bit of research on them",
        "--title",
        "Idea dump tool",
        "--tags",
        "tools, research",
        "--source",
        "my-session",
        "--json",
        data_dir=data,
    )
    assert r.returncode == 0, r.stderr
    idea_id = json.loads(r.stdout)["id"]
    assert idea_id.endswith("-idea-dump-tool")

    note_file = tmp_path / "note.md"
    note_file.write_text("# Prior art\n\nZettelkasten, Obsidian, org-roam.\n")
    r = run_cli("note", "idea-dump", "--file", str(note_file), data_dir=data)
    assert r.returncode == 0, r.stderr

    run_cli("add", "Offline speech to text on the phone", "--tags", "audio", data_dir=data)
    r = run_cli("find", "zettelkasten note taking", data_dir=data)
    assert r.returncode == 0 and idea_id in r.stdout

    r = run_cli("ls", data_dir=data)
    assert "Idea dump tool" in r.stdout and "Offline speech" in r.stdout

    # The folder is browsable: an index at the root, a page per idea, the note beside it.
    assert "Idea dump tool" in (data / "README.md").read_text()
    page = (data / "ideas" / idea_id / "README.md").read_text()
    assert "> I want a place to dump ideas" in page and "Prior art" in page

    r = run_cli("show", "no-such-idea", data_dir=data)
    assert r.returncode != 0 and "ideadump ls" in r.stderr


def test_dol_store_skips_git_folder(tmp_path):
    files = text_files(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("[core]\n")
    add("an idea", files=files, now=NOW)
    assert not any(k.startswith(".git") for k in files)
    assert len(ls(files=files)["ideas"]) == 1


def test_words_kept_and_updates(tmp_path):
    files = {}
    words = "process that wall, organising his ideas"  # a dictation slip, kept as said
    r = add(words, summary="Process them all.", files=files, now=NOW)
    assert show(r["id"], files=files)["record"]["words"] == words
    update(r["id"], status="promising", add_tags="ideas", files=files, now=NOW)
    record = show(r["id"], files=files)["record"]
    assert record["status"] == "promising" and record["tags"] == ["ideas"]
    with pytest.raises(IdeadumpError):
        update(r["id"], status="maybe", files=files)


def test_ids_unique_and_links_both_ways():
    files = {}
    a = add("same title words", title="Same", files=files, now=NOW)["id"]
    b = add("other words", title="Same", files=files, now=NOW)["id"]
    assert a != b and b.endswith("-2")
    link(a, b, why="same thing twice", files=files)
    assert show(a, files=files)["record"]["links"][0]["id"] == b
    assert show(b, files=files)["record"]["links"][0]["id"] == a
    assert "same thing twice" in files[f"ideas/{a}/README.md"]


def test_notes_never_overwrite_and_count_in_search():
    files = {}
    i = add("a tool", title="Tool", files=files, now=NOW)["id"]
    n1 = note(i, text="# One\nquaternion rotations", files=files, now=NOW)["note"]
    n2 = note(i, text="# Two\nmore", depth="light", files=files, now=NOW)["note"]
    assert n1 != n2
    assert find("quaternion", files=files)["hits"][0]["id"] == i


def test_find_from_a_page_of_recent_work(tmp_path):
    files = {}
    add("Route ideas to the agent fleet when relevant work happens", title="Idea routing", files=files)
    add("A sourdough starter schedule", title="Bread", files=files)
    work = tmp_path / "work.md"
    work.write_text("Today: worked on the crowsnest fleet routing of agent sessions; fixed CI.")
    hits = find(file=str(work), files=files)["hits"]
    assert [h["title"] for h in hits] == ["Idea routing"]


def test_parallel_captures_lose_nothing(tmp_path):
    procs = [
        subprocess.Popen(
            [sys.executable, "-m", "ideadump", "add", f"idea {i}", "--title", "Same title"],
            env={**os.environ, "IDEADUMP_DATA_DIR": str(tmp_path)},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        for i in range(6)
    ]
    assert all(p.wait(timeout=60) == 0 for p in procs)
    assert ls(data_dir=tmp_path)["total"] == 6
    assert not (tmp_path / ".ideadump.lock").exists()


def test_errors_say_what_to_do(tmp_path):
    files = {}
    i = add("an idea", files=files, now=NOW)["id"]
    with pytest.raises(IdeadumpError, match="cannot read"):
        note(i, file=str(tmp_path / "missing.md"), files=files)
    with pytest.raises(IdeadumpError, match="not a usable tag"):
        ls(tag=",", files=files)
    with pytest.raises(IdeadumpError, match="status is one of"):
        ls(status="bogus", files=files)
    files[f"ideas/{i}/idea.json"] = "<<<<<<< conflict"
    with pytest.raises(IdeadumpError, match=f"ideas/{i}/idea.json"):
        ls(files=files)


def test_titles_escaped_and_order_across_time_zones():
    files = {}
    add("x", title="A | B [c]", files=files, now="2026-11-14T23:30:00+01:00")
    add("y", title="Later", files=files, now="2026-11-14T22:45:00+00:00")
    assert [r["title"] for r in ls(files=files)["ideas"]] == ["Later", "A | B [c]"]
    assert "A \\| B \\[c\\]" in files["README.md"]


def test_refuses_data_folder_inside_another_work_tree(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    data = tmp_path / "sub" / "ideas"
    monkeypatch.delenv("IDEADUMP_ALLOW_INSIDE_WORK_TREE", raising=False)
    with pytest.raises(IdeadumpError, match="inside the git work tree"):
        add("an idea", data_dir=data)
    monkeypatch.setenv("IDEADUMP_ALLOW_INSIDE_WORK_TREE", "1")
    assert add("an idea", data_dir=data)["id"]

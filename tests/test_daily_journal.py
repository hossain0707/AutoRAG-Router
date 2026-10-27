"""Journal tests use short-lived real local Git repositories and never contact GitHub."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

from scripts.update_daily_log import parse_name_status, update


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], check=True, text=True,
                            capture_output=True)
    return result.stdout.strip()


def _commit(repo: Path, subject: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", subject)
    return _git(repo, "rev-parse", "HEAD")


def _prepare(tmp_path: Path) -> Path:
    repo = tmp_path / "checkout"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "AutoRAG test")
    _git(repo, "config", "user.email", "test@example.invalid")
    (repo / "docs").mkdir()
    (repo / "docs/DAILY_LOG.md").write_text("# Journal\n", encoding="utf-8")
    (repo / "README.md").write_text("old\n", encoding="utf-8")
    (repo / "obsolete.md").write_text("remove me\n", encoding="utf-8")
    (repo / "docs/.journal-state.json").write_text("{}", encoding="utf-8")
    root_sha = _commit(repo, "baseline")
    (repo / "docs/.journal-state.json").write_text(
        json.dumps({"schema_version": 1, "last_processed_sha": root_sha,
                    "last_run_date_kst": "2026-10-26"}), encoding="utf-8")
    return repo


def test_parse_file_statuses():
    raw = "A\tsrc/new.py\nM\tREADME.md\nD\tdocs/obsolete.md\nR100\ta.py\tb.py\n"
    d = parse_name_status(raw)
    assert d == {"added": ["src/new.py"], "modified": ["README.md"],
                 "deleted": ["docs/obsolete.md"], "renamed": ["a.py → b.py"]}


def test_daily_log_records_add_modify_delete_and_no_change(tmp_path):
    repo = _prepare(tmp_path)
    (repo / "README.md").write_text("new\n", encoding="utf-8")
    (repo / "new.txt").write_text("new source\n", encoding="utf-8")
    (repo / "obsolete.md").unlink()
    source_commit = _commit(repo, "feat: edit, add, remove")
    assert update(repo, day="2026-10-27", event="push") is True
    journal = (repo / "docs/DAILY_LOG.md").read_text(encoding="utf-8")
    assert "Added (1)" in journal and "`new.txt`" in journal
    assert "Modified (1)" in journal and "`README.md`" in journal
    assert "Deleted (1)" in journal and "`obsolete.md`" in journal
    assert "feat: edit, add, remove" in journal
    assert source_commit[:12] in journal
    assert update(repo, day="2026-10-27", event="push") is False
    assert update(repo, day="2026-10-28", event="schedule") is True
    assert "No source changes detected" in (repo / "docs/DAILY_LOG.md").read_text()


def test_cursor_catches_unavailable_history(tmp_path):
    repo = _prepare(tmp_path)
    state = repo / "docs/.journal-state.json"
    data = json.loads(state.read_text())
    data["last_processed_sha"] = "a" * 40
    state.write_text(json.dumps(data))
    try:
        update(repo, day="2026-10-29")
    except RuntimeError as error:
        assert "not an ancestor" in str(error)
    else:
        raise AssertionError("Should stop if prior commit cannot be resolved")

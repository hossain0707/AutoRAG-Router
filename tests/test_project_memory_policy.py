"""Verify dated memory format and append-only guard behavior."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_project_memory.py"
spec = importlib.util.spec_from_file_location("project_memory_guard", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def memory(date="2026-10-28", entries=1):
    result = (f"# AutoRAG Router — Project Memory — {date}\n\n"
              "## Current project snapshot\nA.\n\n## Outstanding tasks\nB.\n\n"
              f"## Changes on {date} (Asia/Seoul)\n")
    for i in range(1, entries + 1):
        result += f"\n### Change {i:02d} — Synthetic test\n"
        for name in module.FIELDS:
            result += f"- **{name}:** Recorded.\n"
    return result


def run(cmd, cwd, env):
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, check=False)


def test_valid_daily_doc():
    assert module.validate_document(memory(), "2026-10-28") == []
    assert module.validate_document(memory(entries=2), "2026-10-28") == []


def test_rejects_missing_field_and_duplicate_entries():
    assert module.validate_document(memory().replace("**Fixed:** Recorded.", ""), "2026-10-28")
    assert module.validate_document(memory(entries=2).replace("### Change 02", "### Change 01"), "2026-10-28")


def test_requires_new_change_entry_for_each_push(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    env = os.environ.copy()
    env.update({
        "GIT_AUTHOR_NAME": "Tester", "GIT_AUTHOR_EMAIL": "tester@example.com",
        "GIT_COMMITTER_NAME": "Tester", "GIT_COMMITTER_EMAIL": "tester@example.com",
        "GIT_AUTHOR_DATE": "2026-10-28T12:00:00+09:00",
        "GIT_COMMITTER_DATE": "2026-10-28T12:00:00+09:00",
    })
    assert run(["git", "init", "-q"], repo, env).returncode == 0
    (repo / "src.py").write_text("original\n")
    assert run(["git", "add", "."], repo, env).returncode == 0
    assert run(["git", "commit", "-qm", "initial"], repo, env).returncode == 0

    (repo / "src.py").write_text("changed\n")
    path = repo / "project_memory" / "PROJECT_MEMORY_2026-10-28.md"
    path.parent.mkdir()
    path.write_text(memory())
    assert run(["git", "add", "."], repo, env).returncode == 0
    assert run(["git", "commit", "-qm", "document first push"], repo, env).returncode == 0
    assert run([sys.executable, str(SCRIPT)], repo, env).returncode == 0

    (repo / "src.py").write_text("changed again\n")
    assert run(["git", "add", "."], repo, env).returncode == 0
    assert run(["git", "commit", "-qm", "missing memory"], repo, env).returncode == 0
    failed = run([sys.executable, str(SCRIPT)], repo, env)
    assert failed.returncode != 0 and "did not update" in failed.stderr

    path.write_text(memory().replace("Synthetic test", "Retitled"))
    assert run(["git", "add", "."], repo, env).returncode == 0
    assert run(["git", "commit", "-qm", "changed without new entry"], repo, env).returncode == 0
    failed = run([sys.executable, str(SCRIPT), "--base", "HEAD~2"], repo, env)
    assert failed.returncode != 0 and "append at least one" in failed.stderr

    path.write_text(memory(entries=2))
    assert run(["git", "add", "."], repo, env).returncode == 0
    assert run(["git", "commit", "-qm", "append second entry"], repo, env).returncode == 0
    assert run([sys.executable, str(SCRIPT), "--base", "HEAD~3"], repo, env).returncode == 0

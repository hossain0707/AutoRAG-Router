"""Read-only guard for one-project-memory-file-per-Korean-calendar-day.

Runs inside a Git checkout. Does not write files, commit or push.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import subprocess
import sys

NAME = re.compile(r"^project_memory/PROJECT_MEMORY_(\d{4}-\d{2}-\d{2})\.md$")
ENTRY = re.compile(r"(?m)^### Change (\d{2,}) — .+$")
FIELDS = (
    "KST time", "Task / reason", "Added", "Changed", "Removed", "Fixed",
    "Tests / evidence", "GitHub / deployment", "Decisions", "Risks / blockers", "Next action",
)
KST = timezone(timedelta(hours=9))


def git(*args: str) -> str:
    proc = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if proc.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def date_at_head() -> str:
    stamp = git("show", "-s", "--format=%cI", "HEAD").strip()
    return datetime.fromisoformat(stamp).astimezone(KST).date().isoformat()


def validate_document(content: str, date: str) -> list[str]:
    problems: list[str] = []
    if not content.startswith(f"# AutoRAG Router — Project Memory — {date}\n"):
        problems.append("missing/mismatched dated title")
    for section in ("## Current project snapshot", "## Outstanding tasks", f"## Changes on {date} (Asia/Seoul)"):
        if section not in content:
            problems.append(f"missing section: {section}")
    chunks = ENTRY.split(content.split(f"## Changes on {date} (Asia/Seoul)")[-1])
    numbers = [int(chunks[i]) for i in range(1, len(chunks), 2)]
    if not numbers:
        problems.append("no numbered Change entries")
    elif numbers != list(range(1, len(numbers) + 1)):
        problems.append("Change numbers must be 01, 02, ... without duplication or gaps")
    for index in range(2, len(chunks), 2):
        section = chunks[index]
        for field in FIELDS:
            if not re.search(r"(?m)^- \*\*" + re.escape(field) + r":\*\*\s*\S", section):
                problems.append(f"Change {numbers[(index - 2)//2]:02d} missing nonempty '{field}'")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="HEAD^", help="commit before this push or PR base")
    args = parser.parse_args()
    try:
        date = date_at_head()
        expected = f"project_memory/PROJECT_MEMORY_{date}.md"
        files = [f for f in git("ls-files", "project_memory").splitlines() if f]
        errors = []
        if not files:
            errors.append("project_memory/ has no tracked daily memory file")
        for file in files:
            match = NAME.fullmatch(file)
            if not match:
                errors.append(f"unexpected path (only dated Markdown allowed): {file}")
            else:
                try:
                    datetime.strptime(match.group(1), "%Y-%m-%d")
                except ValueError:
                    errors.append(f"invalid date in filename: {file}")
        if expected not in files:
            errors.append(f"missing today's memory: {expected}")
        else:
            content = Path(expected).read_text(encoding="utf-8")
            errors += validate_document(content, date)
            changed = git("diff", "--name-only", args.base, "HEAD", "--").splitlines()
            if changed and expected not in changed:
                errors.append(f"this push changed files but did not update {expected}")
            if changed and expected in changed:
                try:
                    previous = git("show", f"{args.base}:{expected}")
                except RuntimeError:
                    previous = ""
                count_before = len(ENTRY.findall(previous))
                count_after = len(ENTRY.findall(content))
                if count_after <= count_before:
                    errors.append(
                        f"new push must append at least one Change entry ({count_before} before, {count_after} now)"
                    )
            for file in changed:
                if file.startswith("project_memory/") and file != expected:
                    errors.append(f"past daily memory should not be modified: {file}")
        if errors:
            print("Project memory check FAILED:\n" + "\n".join("- " + e for e in errors), file=sys.stderr)
            return 1
        print(f"Project memory check passed: {expected}")
        return 0
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"Project memory check ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

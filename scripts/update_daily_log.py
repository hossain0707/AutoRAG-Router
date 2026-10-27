#!/usr/bin/env python3
"""Maintain a trustworthy Markdown journal of Git revisions on main.

Only inspects repository Git history and source diffs. No external network,
credentials or cloud APIs are used. Run in a full Git checkout:

    python scripts/update_daily_log.py --repo .

Produces docs/DAILY_LOG.md and docs/.journal-state.json. Commits/pushes are
intentionally left to the reviewed GitHub Actions workflow.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
from zoneinfo import ZoneInfo

STATE = Path("docs/.journal-state.json")
JOURNAL = Path("docs/DAILY_LOG.md")
EXCLUDED = {STATE.as_posix(), JOURNAL.as_posix()}
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True, capture_output=True, check=check,
    )


def parse_name_status(raw: str) -> dict[str, list[str]]:
    """Classify normal Git --name-status text; preserve both rename paths."""
    result: dict[str, list[str]] = {"added": [], "modified": [], "deleted": [], "renamed": []}
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        code = parts[0][0]
        if code in {"R", "C"} and len(parts) >= 3:
            if parts[1] in EXCLUDED and parts[2] in EXCLUDED:
                continue
            result["renamed"].append(f"{parts[1]} → {parts[2]}")
        elif parts[1] not in EXCLUDED:
            bucket = {"A": "added", "D": "deleted"}.get(code, "modified")
            result[bucket].append(parts[1])
    return result


def markdown_safe(text: str) -> str:
    return text.replace("`", "'").replace("\n", " ").replace("\r", " ").strip()


def update(repo: Path, day: str | None = None, event: str = "manual") -> bool:
    """Write an entry only when a new source revision is found or on a new day."""
    repo = repo.resolve()
    state_file, log_file = repo / STATE, repo / JOURNAL
    state = json.loads(state_file.read_text(encoding="utf-8"))
    prior = state.get("last_processed_sha")
    if not isinstance(prior, str) or not GIT_SHA.fullmatch(prior):
        raise ValueError("Journal cursor is missing or invalid; investigate before recovering")
    today = day or datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    current = git(repo, "rev-parse", "HEAD").stdout.strip()
    ancestor = git(repo, "merge-base", "--is-ancestor", prior, current, check=False)
    if ancestor.returncode != 0:
        raise RuntimeError("Journal cursor is not an ancestor of HEAD; do not hide or rewrite history")

    raw = git(
        repo, "diff", "--name-status", "--find-renames", prior, current, "--", ".",
        ":!docs/DAILY_LOG.md", ":!docs/.journal-state.json",
    ).stdout
    changed = parse_name_status(raw)
    commit_raw = git(repo, "log", "--reverse", "--format=%H%x1f%s", f"{prior}..{current}").stdout
    commits = []
    for line in commit_raw.splitlines():
        sha, sep, subject = line.partition("\x1f")
        if sep and not subject.startswith("chore(journal):"):
            commits.append((sha, markdown_safe(subject)))

    actual_changes = sum(map(len, changed.values()))
    if not actual_changes and state.get("last_run_date_kst") == today:
        # Even if no sources changed, advance cursor over a prior journal-only commit.
        if current != prior:
            state["last_processed_sha"] = current
            state_file.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            return True
        return False

    new_lines = [
        f"\n### Auto-captured {today} — {markdown_safe(event)}",
        "",
        f"- **Compared commits:** `{prior[:12]}` → `{current[:12]}`",
        "- **Record source:** Git file history (`main` checkout); not a live deployment check.",
    ]
    if actual_changes:
        new_lines.append(f"- **Files changed:** {actual_changes} path events.")
        for label in ("added", "modified", "deleted", "renamed"):
            items = changed[label]
            if items:
                new_lines.append(f"- **{label.title()} ({len(items)}):**")
                new_lines.extend(f"  - `{markdown_safe(item)}`" for item in items)
    else:
        new_lines.append("- **No source changes detected** since last journal run.")

    if commits:
        new_lines.append("- **Commits observed:**")
        for sha, subject in commits:
            new_lines.append(f"  - [`{sha[:10]}`](https://github.com/hossain0707/AutoRAG-Router/commit/{sha}): {subject}")
    new_lines.append("- **Reminder:** update `PROJECT_CONTEXT.md` / `CHANGELOG.md` manually for new design decisions or deployment changes.")
    new_lines.append("")

    with log_file.open("a", encoding="utf-8") as stream:
        stream.write("\n".join(new_lines))
    state["last_processed_sha"] = current
    state["last_run_date_kst"] = today
    state_file.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."), help="Git checkout root")
    parser.add_argument("--date", help="Override YYYY-MM-DD KST date (for testing)")
    parser.add_argument("--event", default="manual", help="GitHub trigger name")
    args = parser.parse_args()
    changed = update(args.repo, day=args.date, event=args.event)
    print("Journal updated" if changed else "Journal already current")


if __name__ == "__main__":
    main()

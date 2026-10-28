# AutoRAG Router — Change Management and Continuity

Last updated: **2026-10-27**. Repository: https://github.com/hossain0707/AutoRAG-Router.


## Current daily GitHub project memory (effective 2026-10-28)

**The active daily memory is project_memory/PROJECT_MEMORY_YYYY-MM-DD.md.** Files are keyed to the HEAD commit date converted to Asia/Seoul (UTC+09:00); the latest daily file contains a complete current-state snapshot, outstanding tasks and multiple separately numbered change records when several pushes occur that day. The old docs/DAILY_LOG.md is retained as a historical machine journal, not the active per-push handover.

For each owner-authorized GitHub change:
1. Read the last dated memory and verify current source/CI/provider state. Do not assume a previous test or deployment remains valid.
2. Prepare and test code and other docs. Draft today's daily Markdown file from the current verified snapshot.
3. Append **one new numbered Change entry per approved push**, with fields KST time; task/reason; added; changed; removed; fixed; tests/evidence; GitHub/deployment; decisions; risks/blockers; next action. Record "None" or "Not tested" where appropriate.
4. On a second, third or fifth approved push on that date, **edit the exact same file** and append Change 02, Change 03, Change 05, etc. No filename suffix or multiple files for a date. Preserve all previous entries; correct historical errors in today's file instead of silently changing prior days.
5. Run **python scripts/check_project_memory.py --base HEAD^** or use the read-only CI guard. CI rejects missing/incorrect dates and same-day pushes with no newly appended entry; it cannot confirm factual truth.
6. Obtain explicit owner approval for the particular GitHub push or any deployment. GitHub CI **never commits/pushes the memory itself**. A file cannot know its containing commit's SHA in advance; verify links after commit and use Git history as proof. A separate follow-up entry can record the SHA with the next approved change.

Only date-stamped Markdown memory files belong inside project_memory/. Keep validation code in scripts/ and tests/. Do not place tokens, customer data, datasets, LLM answers, weights or artifacts in memory. Existing ChatGPT Project Sources attachments do not automatically synchronize with GitHub; update those separately when requested.

Read-only CI command: **python scripts/check_project_memory.py --base <previous-main-sha>** for a push or **--base <pull-request-base-sha>** for a PR. If the repo change spans multiple days, align the latest commit date and the daily file or split the changes into appropriately dated approved pushes. This policy does **not** re-enable the historical scheduled GitHub journal.

## Binding owner preference: no automatic GitHub writes

**Never automatically commit, push, merge, publish releases, deploy, or change remote files.** GitHub writes require an explicit request or approval from the owner for the particular change. The earlier daily automatic GitHub journal was disabled on 2026-10-27. Existing records remain preserved.

Read-only daily status checking and reporting may continue. Reviewers should prepare changes locally and present them for approval before any GitHub write. This rule overrides any old instructions in past chats.

## Source-of-truth files

| File | Meaning | Update rule |
| --- | --- | --- |
| [PROJECT_CONTEXT.md](../PROJECT_CONTEXT.md) | Full project history, owner decisions, verified account identifiers, risks and next steps | Draft when material facts change; publish only on explicit request |
| [AGENTS.md](../AGENTS.md) | Rules for all coding agents and future chats | Owner-approved updates only |
| [CHANGELOG.md](../CHANGELOG.md) | Human-readable added/changed/fixed/removed records | Alongside explicitly approved substantive changes |
| [DAILY_LOG.md](DAILY_LOG.md) | Historical Git-derived file/commit journal | No scheduled commits; update only if owner requests |
| [.journal-state.json](.journal-state.json) | Incremental journal cursor | Keep with journal; do not rewrite without checking ancestry |
| [../README.md](../README.md) | Installation, implementation limitations, links, license | Update with an owner-approved release |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Technical design and threat model | Update with an owner-approved technical change |

## Journal: manual preview, never push

`.github/workflows/daily-project-journal.yml` **no longer has `push` or `schedule` triggers** and uses `contents: read`. It can run via an intentionally requested `workflow_dispatch`. That runner generates a **temporary local preview** using `scripts/update_daily_log.py`, prints a summary, and finishes **without committing or pushing**.

To preview locally in a full Git checkout:

```bash
python scripts/update_daily_log.py --repo . --event manual_preview
git diff -- docs/DAILY_LOG.md docs/.journal-state.json
```

These commands change local working-copy files only. Do not stage, commit or push the output without explicit authorization. Do not enable scheduled or push-triggered publishing without a new owner request.

## Read-only daily ChatGPT project review

The **AutoRAG daily read-only review** automation may inspect repo files, commits, CI, verified Vercel deployment state and the public demo, then report meaningful differences. It **must not** update source files, commit, push, deploy, trigger write workflows or modify cloud settings. It is informational, not self-updating project memory.

## Workflow for future changes

1. Read `PROJECT_CONTEXT.md`, `AGENTS.md`, `CHANGELOG.md`, the latest journal and implementation before proposing changes.
2. Inspect the current GitHub `main` revision, existing tests and Vercel deployment when relevant. Do not assume old statuses remain true.
3. Plan and implement requested changes in a draft/local workspace; add regression tests and run applicable checks.
4. Prepare a changelog and context update to accompany the change. Explain added, changed, removed or broken features.
5. **Only after explicit owner authorization for GitHub writes**, create a commit/push; report exact commit SHA and verify CI results.
6. **Only after separate approval if deployment is needed**, deploy and verify the public URL with real browser interactions. A GitHub push alone does not automatically redeploy Vercel.
7. If the user only asks to review, explain or suggest, do not push code.

## GitHub and Vercel identifiers (non-secret)

- GitHub repository: https://github.com/hossain0707/AutoRAG-Router, branch `main`.
- Vercel project: `autorag-router-demo`; project ID `prj_dm2L1KNIrOUEX9it40yaUpyMgF30`; team ID `team_ld0IOXvEO5BtaXuCppcBNKHJ`.
- Vercel dashboard: https://vercel.com/najmuleee1996-6229s-projects/autorag-router-demo
- Production demo: https://autorag-router-demo.vercel.app/
- Last verified Vercel production deployment (2026-10-27): `dpl_EoAEbCTLC3F5yJg1WWTZ2w6Evuiy`, `READY`. Re-check before relying on it.
- Public Vercel site is a **browser-side JavaScript demo**; the local Python FastAPI backend is not hosted there.
- Last observed Vercel deployment files: `src/index.html`, `src/app.js`, `src/styles.css`. GitHub's source files are under `docs/`; automatic synchronization to Vercel is **not established**.
- Optional GitHub Pages workflow remains manual-only and the Pages URL was previously unavailable.

Never store GitHub tokens, Vercel credentials, `.env` values or private user data in public handover files.

## Ready-to-use prompt for a new chat

> Continue `hossain0707/AutoRAG-Router`. Read `PROJECT_CONTEXT.md`, `AGENTS.md`, `CHANGELOG.md`, `docs/DAILY_LOG.md` and `docs/WORKFLOW.md`, then inspect the current GitHub and Vercel state. Keep all work read-only unless I explicitly authorize the particular GitHub write or deployment. Report accurate findings, prepare changes for my approval, and never automatically commit or push.

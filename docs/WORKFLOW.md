# AutoRAG Router — Change Management and Continuity Workflow

**Purpose:** make project context durable across ChatGPT chats, Codex sessions, cloud machines, contributors and deployments. Public repository: https://github.com/hossain0707/AutoRAG-Router.

## Files and ownership

| File | Responsibility | How updated |
| --- | --- | --- |
| [`../PROJECT_CONTEXT.md`](../PROJECT_CONTEXT.md) | Product goal, architecture, current reality, deployment identifiers and evidence, open problems, next actions | A human or agent **after every material change**, with verification |
| [`../AGENTS.md`](../AGENTS.md) | Mandatory instructions to any new agent | Human-reviewed when policies change |
| [`../CHANGELOG.md`](../CHANGELOG.md) | Why/what changes, improvements/removals, version/release notes | With every user-impacting change |
| [`DAILY_LOG.md`](DAILY_LOG.md) | Git-derived file/commit change log; dates and added/changed/deleted/renamed files | GitHub Action on `main` pushes and **daily** |
| [`.journal-state.json`](.journal-state.json) | Git commit cursor for incremental journal | Script-owned; do not edit manually except to recover |
| [`../README.md`](../README.md) | Public-facing installation/architecture/demo and license terms | With functionality or release changes |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Engineering architecture/security limits | With substantive design/security changes |

## Daily scheduled change capture

Workflow: `.github/workflows/daily-project-journal.yml`, script `scripts/update_daily_log.py`. Schedule: `0 0 * * *` UTC = **09:00 Asia/Seoul** daily (GitHub schedule may be delayed); also runs on pushes to `main`, and allows manual `workflow_dispatch`.

Script workflow:

1. Checkout complete `main` history and read `docs/.journal-state.json` as the previous processed Git SHA.
2. Compare **previous SHA → current HEAD**, excluding journal-managed files, and classify added (`A`), modified (`M`), deleted (`D`) and renamed (`R`) paths.
3. Record actual commit summaries, source SHA range, and dated results in `docs/DAILY_LOG.md`.
4. If no source changes occurred, record a daily **no-source-change** entry instead of inventing work.
5. Update cursor and commit/push changes back to `main` using the repository's GitHub Actions token.

**The journal workflow does not silently deploy Vercel, change the user-facing README, or write subjective architectural conclusions.** It cannot infer intent from diff alone; a human/agent must update `PROJECT_CONTEXT.md` and `CHANGELOG.md` with reasoning. When GitHub Actions is disabled, a workflow run fails, or branch protection disallows writes, journal entries will **not** be created automatically. Inspect workflow history; do not claim continuous tracking without evidence.

## Procedure after any source change (applies in every chat)

1. Fetch latest GitHub `main`; read `PROJECT_CONTEXT.md`, `AGENTS.md`, `CHANGELOG.md` and the most recent daily log entry before edits.
2. Record issue/task goal and acceptance criteria. Distinguish verified current behavior vs proposed improvements.
3. Edit implementation, add regression tests, run Python, JS and relevant browser tests; record failures candidly.
4. Update `CHANGELOG.md` with date and **Added / Changed / Removed / Fixed / Security / Tests** as appropriate; update `PROJECT_CONTEXT.md` for new verified status, risks and decisions.
5. Commit, push and verify the SHA. Observe CI, inspect the journal run and check Vercel deployment if changed.
6. After a deployed frontend modification, test `https://autorag-router-demo.vercel.app/` in a real browser with Graph and Structured scenarios; compare deployed JS/HTML to GitHub `docs/` source.
7. Do not close the task if the promised public demo or actual runtime behavior has not been verified; clearly state limitations.

## Deployment reality and reproducibility

- `README.md` Live Demo: https://autorag-router-demo.vercel.app/
- Vercel project ID: `prj_dm2L1KNIrOUEX9it40yaUpyMgF30`; team ID: `team_ld0IOXvEO5BtaXuCppcBNKHJ`.
- Last verified production snapshot: `dpl_EoAEbCTLC3F5yJg1WWTZ2w6Evuiy` (`READY`, 2026-10-27).
- Source in last Vercel deployment: `src/index.html`, `src/app.js`, `src/styles.css`; repository browser demo source: `docs/index.html`, `docs/app.js`, `docs/styles.css`.
- Dashboard screenshot indicated **Connect Git Repository** and deployment source `vercel deploy`. As of that verification, auto-deploy from GitHub pushes **was not established**.
- GitHub Pages URL previously failed. Its optional workflow does not mean the domain is live.
- Deployment secrets must be set only through protected Vercel/GitHub secret storage. Do not store personal session/cookies or tokens in Markdown.

To deploy a revised demo: (a) verify project/team identity; (b) link the correct GitHub source/build root if approved, or explicitly deploy the `docs/` static directory via authenticated Vercel tool/CLI; (c) inspect the new deployment state, alias and files; (d) run real browser smoke tests; (e) update the canonical context with observed deployment SHA/URL and test result. Git commit alone is NOT deployment verification.

## Recovery from a broken daily journal

- Open https://github.com/hossain0707/AutoRAG-Router/actions/workflows/daily-project-journal.yml and examine latest failure.
- Confirm GitHub Actions is enabled and `GITHUB_TOKEN` has `contents: write` and branch allows bot commits; if branch protections disallow it, use an approved PR-based strategy rather than bypassing security.
- Script can run manually from a **real Git clone**: `python scripts/update_daily_log.py --repo .`. Commit the produced `docs/DAILY_LOG.md` and `docs/.journal-state.json` together.
- Do not delete/reinitialize the cursor unless intentionally backfilling; it prevents lost/duplicate diff windows.
- Do not edit existing journal entries to rewrite history. Add corrective entries instead.
- If the cursor SHA is not available or is no longer an ancestor of HEAD, stop and investigate history rewrites before resuming.

## Default next-session prompt

> Continue `hossain0707/AutoRAG-Router`. Read `PROJECT_CONTEXT.md`, `AGENTS.md`, `CHANGELOG.md`, `docs/DAILY_LOG.md`, `docs/WORKFLOW.md` and code. Check the latest GitHub commits, Actions and current Vercel production deployment. Explain what exists and what remains, perform requested engineering work, run reproducible tests, update those Markdown handover records for any verified changes, and push the changes. Never include secrets or claim nonexistent capabilities.

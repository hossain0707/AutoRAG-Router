# AutoRAG Router — Human-Curated Changelog

This file records **why** functionality changed, what was **added / changed / removed**, impact, verification, and follow-up. For historical commit-level file lists, see the [previously generated Git journal](docs/DAILY_LOG.md); it is not a substitute for this editorial history.

## [Unreleased]


### Added — 2026-10-28 (GitHub daily project memory policy)

- Owner-approved **project_memory/PROJECT_MEMORY_2026-10-28.md**, containing an up-to-date project snapshot, open tasks and separate records of the benchmark delivery and new daily-memory process.
- Read-only **scripts/check_project_memory.py** and **tests/test_project_memory_policy.py** to check one dated Markdown file per KST day, a fresh numbered entry for each changed push, and preservation of prior-day files. Three local policy tests passed in a temporary Git repository; complete GitHub CI must be verified after this commit.
- Updated agent, contributor, workflow, README and handover instructions, plus GitHub CI checks. **No scheduled writes, automatic pushes, Vercel deployments, benchmark model downloads or scientific claims** are introduced.


### Added — 2026-10-28

- Isolated `benchmarks/` evaluation package with toy/BEIR/RAGRouter-Bench dataset adapters, provenance-preserving chunking, actual engine and fixed lexical baselines, opt-in loopback-only Qwen/vLLM client, retrieval/routing/lexical-answer metrics, resumable run fingerprints and JSON/Markdown reports.
- Added benchmark regression tests and a synthetic, offline CI smoke/report step. Initial local validation on x86_64 Python: 24 tests passed, Python compilation and JS syntax checks passed; one 15-evaluation synthetic run completed. **DGX Spark, Qwen model inference, external benchmark runs and full GraphRAG/IterativeRAG parity have not been tested or claimed.**
- Benchmark instructions, hardware checks and source documentation. No model weights or datasets committed. No GitHub auto-push workflow, Vercel deployment or production API alteration.



### Changed — 2026-10-27 (owner instruction)

- **Disabled all automatic journal commits and pushes.** The journal workflow is manual-dispatch only, requests read-only repository permission, and previews changes without committing or pushing.
- Updated daily ChatGPT AutoRAG review to read-only reporting; it may not modify GitHub or Vercel.
- Future repository edits, documentation commits and deployments require the owner's explicit case-by-case authorization. Preserved all historical journal entries and source files; regular CI still runs tests on pushes but does not publish files.


### Added — 2026-10-27

- Canonical cross-chat project handover (`PROJECT_CONTEXT.md`) and agent rules (`AGENTS.md`).
- Documented workflow for maintaining project decisions, cloud resource identifiers, limitations and quality evidence (`docs/WORKFLOW.md`).
- Scheduled GitHub Actions journal and incremental Git diff recorder (`.github/workflows/daily-project-journal.yml`, `scripts/update_daily_log.py`, `docs/DAILY_LOG.md`).
- Automated tests for journaling and file-change classification (`tests/test_daily_journal.py`).
- A separate **daily ChatGPT project sync** to review GitHub/Vercel drift and update verified handover facts when connected permissions permit.

### Changed

- README now links new developers to the canonical handover and history. Future meaningful modifications must update both code and relevant context records.
- Made the optional GitHub Pages publication workflow **manual-only** while Pages is not enabled; the primary live demo remains on Vercel. The 2026-10-27 automatic Pages run failed at `Configure GitHub Pages` with Not Found.

### Limitations

- Journal only sees Git content/history, not changes made directly in Vercel or external infrastructure; those require live verification and human/agent annotation.
- **Superseded:** the original daily push-enabled journal was disabled by owner request on 2026-10-27. There are no authorized scheduled journal pushes.

## [0.1.0 developer preview] — 2026-10-27

### Added

- Task-adaptive deterministic `no_rag`, `hybrid`, `graph`, `agentic`, `multimodal` and `structured` routing; API and local SQLite store.
- BM25 + character-trigram lexical/fuzzy fusion; tagged-entity graph lookup; bounded query decomposition; metadata-based structured retrieval; extractive evidence and fallback.
- FastAPI, CLI, local dashboard, Docker Compose, initial Python tests and CI workflow. **16 local tests passed at release time.**
- Architecture and API documentation, animated demos, conceptual promo video.
- Live interactive static HTML/CSS/JavaScript browser demo with actual local policy execution and seven synthetic source records; real UI-recorded MP4, GIF and screenshot.
- GitHub Pages workflow as an optional deployment method; Vercel project `autorag-router-demo` deployed as public static site with production `READY` snapshot.

### Changed

- Changed current repository distribution license from **MIT** to **Personal Noncommercial License v1.0**. Individual noncommercial use permitted; commercial use requires separately negotiated written permission. The new license does not retroactively revoke earlier valid MIT grants.
- Changed README Live Demo links from unconfigured GitHub Pages to `https://autorag-router-demo.vercel.app/` after Pages returned “Site not found.”

### Removed / replaced

- Removed **MIT licensing from current main**, replacing it with the noncommercial license (historically granted MIT rights remain applicable to earlier distributions).
- Replaced the **broken GitHub Pages link as the primary Live Demo destination** with Vercel. The optional Pages publishing workflow remains in repository.

### Verification and known issues

- Local Python tests: 16 passed at first release. Live browser test: page + JavaScript loaded; Graph sample returned three evidence passages; Structured revenue sample selected correct strategy and showed results/traces.
- **Open issue:** Structured revenue retrieval returns unrelated results with misleadingly high scores; quality and calibration fixes are needed.
- Vercel demo does not host a Python API, LLM, vector index, external graph DB or real image understanding. CI status and deployment parity must be rechecked for each revision.

### Commits (2026-10-27)

- [`8edcdce`](https://github.com/hossain0707/AutoRAG-Router/commit/8edcdce2ce26cb5a948fdb82a5b9dfc5ffc6474a) — repository initialization.
- [`e9bddf2`](https://github.com/hossain0707/AutoRAG-Router/commit/e9bddf2d39356375240f8f21c50bae4ca30b5f76) — temporary source unpack workflow.
- [`201b605`](https://github.com/hossain0707/AutoRAG-Router/commit/201b605a126a8fa6b78952cf8f13bb4d8f1634dd) — staged source bundle.
- [`fd1648e`](https://github.com/hossain0707/AutoRAG-Router/commit/fd1648e60dd8da4d043c8fccba14b0db99ee0ba7) — first tested package and README.
- [`db7d6a1`](https://github.com/hossain0707/AutoRAG-Router/commit/db7d6a11065849ccbb6ba1be09b3fa90f9debd7e) — animated GIF.
- [`1dd8e07`](https://github.com/hossain0707/AutoRAG-Router/commit/1dd8e074fba3a8beb21e40c384b059b5eabe495c) — promo video.
- [`a388469`](https://github.com/hossain0707/AutoRAG-Router/commit/a388469b8950baf9522400eeb744ef42401a38f3) — live browser demo + real animation + noncommercial license.
- [`6e8add7`](https://github.com/hossain0707/AutoRAG-Router/commit/6e8add7df409a8b6fe47776922f5a39acb97babe) — README links corrected to Vercel.

**How to update this file:** add each substantial change under Unreleased with date, rationale, behavior change, testing, security consequences and a source commit/PR URL. At a version release, move Unreleased entries into a new dated version section, and keep all earlier history.

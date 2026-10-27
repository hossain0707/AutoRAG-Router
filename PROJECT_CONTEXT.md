# AutoRAG Router — Canonical Project Handover

> **START HERE for any new ChatGPT chat, Codex session, developer or agent.**
> Last manually verified: **2026-10-27 (Asia/Seoul)**. Status entries below are a dated snapshot, not a guarantee of perpetual uptime.
> Owner: **Md Najmul Hossain** · GitHub: **[@hossain0707](https://github.com/hossain0707)** · Project: **AutoRAG-Router** · Version: **0.1.0 developer preview**.

## Owner override — 2026-10-27

**NO AUTOMATIC GITHUB PUSHES OR COMMITS.** The owner withdrew the earlier request for daily automatic GitHub writes. GitHub Actions journal is **manual, read-only preview** only, and the daily ChatGPT automation is **read-only**, allowed to report changes but forbidden to update GitHub or Vercel. Any GitHub change or deployment requires explicit case-by-case user authorization. No scheduled bot commits/pushes. This current directive supersedes earlier references below to auto-maintained files.

## 0. Continuity protocol — read before editing

1. Read **this entire file**, [`AGENTS.md`](AGENTS.md), [`README.md`](README.md), [`CHANGELOG.md`](CHANGELOG.md), [`docs/DAILY_LOG.md`](docs/DAILY_LOG.md), [`docs/WORKFLOW.md`](docs/WORKFLOW.md) and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
2. Inspect the **current** `main` branch, actual source, CI, Vercel deployment and recent commits; dated snapshots can become stale. Cross-check claims before repeating them.
3. State what is implemented vs simulated/demo-only vs planned. Preserve the distinction between **browser demo** and **Python API**.
4. After **every material change**, update this document if an architectural decision, status, deployment, risk or next action changed. Add a human-understandable entry to `CHANGELOG.md` and ensure tests cover code changes. The historical Git journal can be regenerated manually when requested but **must not automatically commit or push**.
5. Never put API tokens, login cookies, passwords, `.env` contents, SSH keys, user data or private infrastructure details in this public repository.
6. Do not claim the GitHub Pages site works unless verified; use the verified Vercel link as the README's Live Demo destination.
7. New chats should begin with: **“Read `PROJECT_CONTEXT.md`, `AGENTS.md`, `CHANGELOG.md`, and the latest `docs/DAILY_LOG.md` in `hossain0707/AutoRAG-Router`; inspect current GitHub and Vercel state before edits; continue from the open tasks.”**

## 1. Purpose and vision

The user proposed **task-adaptive RAG selection**, analogous to automatically routing an incoming request to an LLM: analyze the question/task and select the best retrieval method, possibly composing multiple methods; only invoke retrieval when needed. The independent framework should be usable by third-party apps and optionally by the user's **NEXUS-100** agent platform.

**Long-term vision:** model-independent, cost-/latency-/quality-aware, multi-strategy RAG orchestration with scored evidence, telemetry, guarded fallbacks, dynamic routing and learned improvement based on validated benchmarks.

**Present reality:** a deterministic, rule-based, explainable **local-first developer-preview baseline** with six strategy labels and lightweight offline retrieval; no full neural RAG stack, trained meta-router or autonomous agents yet.

Avoid treating GraphRAG, Hybrid, Agentic, Self-RAG and CRAG as mutually exclusive full algorithms. The architecture should evolve toward **composable retrieval and validation capabilities**, not marketing-only method names.

## 2. Accounts, repositories, deployments — non-secret identifiers

| Resource | Verified identifier or URL | Interpretation |
| --- | --- | --- |
| GitHub repository | https://github.com/hossain0707/AutoRAG-Router | Public, default `main`; GitHub repository ID `1435298760` |
| Clone URL | https://github.com/hossain0707/AutoRAG-Router.git | Repository source |
| GitHub owner | `hossain0707` | Md Najmul Hossain; connected GitHub app had write permissions at last check |
| Vercel project | `autorag-router-demo` | **Static browser-side HTML/CSS/JS demo**, not Python FastAPI |
| Vercel project ID | `prj_dm2L1KNIrOUEX9it40yaUpyMgF30` | Public identifier, not a token |
| Vercel team ID | `team_ld0IOXvEO5BtaXuCppcBNKHJ` | Public-ish internal resource identifier, not credentials |
| Vercel team slug | `najmuleee1996-6229s-projects` | Dashboard scope |
| Vercel dashboard | https://vercel.com/najmuleee1996-6229s-projects/autorag-router-demo | Requires authorized login |
| Production demo | **https://autorag-router-demo.vercel.app/** | The supported README Live Demo link |
| Production deployment snapshot | `dpl_EoAEbCTLC3F5yJg1WWTZ2w6Evuiy` | `READY` at 2026-10-27 check; may change after redeploys |
| Deployment inspection | https://vercel.com/najmuleee1996-6229s-projects/autorag-router-demo/EoAEbCTLC3F5yJg1WWTZ2w6Evuiy | Deployment snapshot |
| GitHub Actions | https://github.com/hossain0707/AutoRAG-Router/actions | Read-only CI, optional manual Pages, manual-only journal preview (no auto push) |
| GitHub Pages | https://hossain0707.github.io/AutoRAG-Router/ | **Previously “Site not found”; `pages.yml` failed at Configure GitHub Pages (Get Pages site: Not Found); do NOT use as primary live demo** |

### Vercel operating facts, verified 2026-10-27

- Authenticated Vercel connector access **was approved and verified** for the team above during this work; future sessions must reauthorize if permissions expire.
- Project `autorag-router-demo` had a **production deployment `READY`**, production alias `autorag-router-demo.vercel.app`, no password/SSO restriction, runtime Node 24.x.
- Deployment files were `src/index.html`, `src/app.js`, `src/styles.css` (the browser demo).
- Project showed no connected Git repository in the dashboard screenshot; deployment source indicated `vercel deploy`. **Do not assume that pushing GitHub `docs/` automatically updates Vercel.** Redeploy or connect Git explicitly and verify new runtime and public domain after changes.
- The repo's `docs/index.html`, `docs/app.js`, and `docs/styles.css` are the intended source for the static demo; confirm parity with deployed Vercel files after any frontend change.
- In a live browser smoke test on 2026-10-27: Graph example routed to **Graph RAG**, retrieved **3** source passages, showed `policy:graph`, `retrieved:3`, `evidence_check:pass`; revenue example routed to **Structured RAG**, with evidence and trace. Public site and client-side JavaScript loaded. **This is not proof of server-side Python or production-scale quality.**

**Security:** record IDs and URLs, not credentials. Never print or store a Vercel token, GitHub token or production secrets in this file or commits.

## 3. Current implementation inventory (v0.1.0)

### Python package/API

- `autorag/router.py`: explainable deterministic query-intent routing; explicit override supported; route labels `no_rag`, `hybrid`, `graph`, `agentic`, `multimodal`, `structured`.
- `autorag/retrieval.py`: BM25 lexical + **character-trigram cosine** fuzzy similarity, reciprocal rank fusion (RRF), one-hop entity-tag lookups, bounded query decomposition, metadata filters.
- `autorag/engine.py`: dispatches retrieval, fallback to Hybrid on zero hits for specialized routes, heuristic evidence check, extractive snippets and request trace. **No LLM-generated final answer.**
- `autorag/store.py`: tenant-partitioned SQLite storage, appropriate for local/single-instance use; tenant IDs provided by callers are not authorization.
- `autorag/api.py`: FastAPI; document ingest, query, metrics, Swagger and HTML local dashboard; optional deployment-wide `AUTORAG_API_KEY` header.
- `autorag/models.py`: bounded Pydantic input/output contracts.
- `autorag/cli.py`, `autorag/static/index.html`: local CLI and Python API dashboard.
- `Dockerfile`, `compose.yml`, `.env.example`, `pyproject.toml`: packaging and local deployment; Python >=3.11.
- `tests/`: deterministic routing/engine/API tests. **16/16 tests passed locally when first released 2026-10-27**; rerun on subsequent changes rather than assuming.

### Public browser demo (different runtime)

- `docs/index.html`, `docs/styles.css`, `docs/app.js`: interactive browser-only routing playground running a JavaScript implementation of the policy and local text retrieval. Has synthetic Atlas/Beacon, policies, finance, diagram-caption examples; user input and added non-sensitive documents stay in browser memory.
- `assets/real-router-walkthrough.gif`, `.mp4`, `real-routing-preview.png`: real browser interaction recordings/screenshot.
- `assets/AutoRAG_Router_Promo.mp4`: short promotional concept video, **not proof of backend capabilities**.
- `scripts/capture_live_demo.py` and `scripts/make_promo.py`: asset-generation workflows.
- No cloud LLM, native vision encoder, remote vector DB or persistent server API is invoked by the hosted browser demo.

### Exactly what each strategy means today

| Strategy | Actual behavior | Not yet present |
| --- | --- | --- |
| No-RAG | skip document retrieval for trivial dialogue | LLM chatbot generation |
| Hybrid | BM25 + character trigram fuzzy similarity + RRF | semantic neural embeddings, dense vector search engine, reranker |
| Graph | overlap among explicitly tagged entities; one-hop | true knowledge graph with relational edge semantics/multi-hop |
| Agentic-style | bounded query decomposition then hybrid retrieval | autonomous tool-using/planning agents |
| Multimodal-text | retrieves already extracted captions, PDF text and table text | direct image/PDF perception or OCR |
| Structured | metadata filtering plus lexical/fuzzy search | governed SQL execution, trustworthy arithmetic aggregation |
| Corrective/Evidence check | fallback on no hits; presence/score heuristic | trained evidence grader, Self-RAG/CRAG algorithms or claim-level verification |

**Scores are ranking heuristics; the UI's “policy score” is not statistically calibrated confidence.**

## 4. Validation, limitations and current open issues

**Verified functioning** (2026-10-27): hosted page and JavaScript loaded, synthetic records populated (7 at test time), click-to-route worked, Graph and Structured scenarios showed result lists and execution traces. Previous local Python test suite reported 16 passing tests. Further benchmarks and CI state must be checked afresh.

**Known problem (high priority):** Structured RAG revenue demonstration returned **5** records including unrelated architecture/HR/security documents. Relevant revenue document ranked first, but irrelevant results had misleadingly high display scores. Improve filtering, ranking calibration, top-k evidence thresholding, semantic isolation and regression tests before claiming excellent precision. No issue has been conclusively resolved yet.

**Production risks:** no identity-derived tenant authorization; no API rate limiter or public multi-tenant hardening; SQLite local store; non-neural retrieval; no genuine agentic tool execution; no image understanding; no rigorous ground-truth benchmark for routing quality/cost/latency; generic fallback criteria; low evidentiary rigor; possible prompt-injection considerations when integrating future LLMs. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

**Novelty position:** Automatic RAG method selection is an established research/engineering direction. This framework is **partially differentiated as an integrated implementation**, **not currently a scientifically novel RAG algorithm**. Potential research contributions: adaptive compositional policies, budget-aware bandit/meta-learning, quality-aware fallback, reproducible evaluation and demonstrated improvement over fixed RAG baselines. Do not claim a novel paper-ready method without literature review and experiments.

## 5. License and IP decision

**`LICENSE`: AutoRAG Router Personal Noncommercial License v1.0.** Individual personal, hobby, educational and unpaid noncommercial research use permitted subject to terms. Commercial internal company usage, SaaS/API, embedded paid products, consulting or monetized services require a **separately negotiated written license**. Commercial contact: https://github.com/hossain0707 or repo issue. This is **source-available, not OSI open source**.

History: initial v0.1.0 was MIT-licensed, followed by the personal-noncommercial license on **2026-10-27**. Previous valid MIT grants cannot be retroactively revoked by changing current repository license. Avoid asserting exclusivity over old releases.

## 6. Dated project decision and delivery history

All events below are **2026-10-27 (Korea local date)**; commit timestamps are UTC. Exact verified Git history:

| Commit | Change (user-facing meaning) |
| --- | --- |
| [`8edcdce`](https://github.com/hossain0707/AutoRAG-Router/commit/8edcdce2ce26cb5a948fdb82a5b9dfc5ffc6474a) | Initialize repository. |
| [`e9bddf2`](https://github.com/hossain0707/AutoRAG-Router/commit/e9bddf2d39356375240f8f21c50bae4ca30b5f76) | Added one-time unpack workflow during bootstrap. |
| [`201b605`](https://github.com/hossain0707/AutoRAG-Router/commit/201b605a126a8fa6b78952cf8f13bb4d8f1634dd) | Staged source bundle for bootstrap. |
| [`fd1648e`](https://github.com/hossain0707/AutoRAG-Router/commit/fd1648e60dd8da4d043c8fccba14b0db99ee0ba7) | Released v0.1.0 package, local dashboard/API, CI/tests/docs. Initial license was MIT. |
| [`db7d6a1`](https://github.com/hossain0707/AutoRAG-Router/commit/db7d6a11065849ccbb6ba1be09b3fa90f9debd7e) | Added short animated routing demo GIF. |
| [`1dd8e07`](https://github.com/hossain0707/AutoRAG-Router/commit/1dd8e074fba3a8beb21e40c384b059b5eabe495c) | Added short promotional MP4. |
| [`a388469`](https://github.com/hossain0707/AutoRAG-Router/commit/a388469b8950baf9522400eeb744ef42401a38f3) | Added functioning browser demo, real GIF/MP4 and screenshot, changed license to noncommercial, added Pages workflow. |
| [`6e8add7`](https://github.com/hossain0707/AutoRAG-Router/commit/6e8add7df409a8b6fe47776922f5a39acb97babe) | Fixed all README Live Demo links from broken GitHub Pages address to public Vercel domain. |

User requirements resolved: independent framework rather than hard-coupled NEXUS-100; professional README with authentic animation; public interactive HTML preview; free personal, paid commercial only on contact; verifiable live demo button. User asked for durable cross-chat source context and initially a daily change record; **later on 2026-10-27 explicitly withdrew authorization for automatic GitHub pushes**. The final owner decision is **read-only monitoring, manual GitHub updates only when explicitly requested**.

## 7. Next priorities / acceptance criteria

1. **Fix Structured RAG result precision** for revenue sample, both browser demo and Python strategy: unrelated records must not masquerade as strong supporting evidence; add measured regression tests.
2. Establish **deployment parity and CI/CD** between `docs/` on GitHub and actual Vercel `src/` deployment; ideally connect the Git repository to Vercel or document a reproducible explicit build/redeploy process. Never silently imply GitHub automatically deploys Vercel.
3. Implement **measurable benchmark suite**: labeled query→strategy tasks, positive and negative retrieval ground truth, Recall@k, nDCG, evidence faithfulness, latency, cost, fallback triggers, confusion matrix; compare fixed Hybrid vs adaptive vs oracle.
4. Design **pluggable retrieval contracts** for dense neural embeddings (Qdrant/pgvector), reranking, knowledge graphs (Neo4j), governed SQL, and future multimodal components.
5. Introduce **identity-aware authorization, tenant isolation, rate limits, audit logs, observability and deployment review**, before offering enterprise/API access.
6. Explore **scientific novelty** through budget-constrained strategy composition and feedback-driven improvement, tested on reproducible public/permissioned data.
7. Keep `README.md`, this handover, `CHANGELOG.md` and `docs/DAILY_LOG.md` synchronized with verifiable implementation and deployment evidence.

## 8. How to run and test

```bash
git clone https://github.com/hossain0707/AutoRAG-Router.git
cd AutoRAG-Router
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest -q
python -m compileall -q autorag
node --check docs/app.js
autorag serve
# Local API: http://127.0.0.1:8000/docs
```

For optional Docker: configure a private `AUTORAG_API_KEY` in `.env` based on `.env.example`, then `docker compose up --build`. Do not commit `.env` or expose the insecure demo/API publicly.

### Daily and per-change recording

- `CHANGELOG.md`: curated human summary (release-impacting decisions, new features and removals).
- `docs/DAILY_LOG.md`: historical journal only. No scheduled GitHub writes; optional `.github/workflows/daily-project-journal.yml` can be manually dispatched for an ephemeral read-only preview and does not commit/push. Publish new journal entries only with explicit owner permission.
- `docs/.journal-state.json`: last inspected Git commit for incremental changelog; this is a machine cursor, not a credential.
- `scripts/update_daily_log.py`: computes commit and file change summary, including added/modified/deleted/renamed files; records days with no source changes.
- `AGENTS.md`: behavior contract for any assistant; documentation updates are part of the definition of done.
- `docs/WORKFLOW.md`: exact operations and recovery instructions.
- **Daily GitHub file diff cannot observe external Vercel changes or record human intent.** Manually verify production deployments, annotate decisions and update status after a rollout. The independent scheduled assistant review is read-only and cannot write to GitHub, Vercel or any other deployment.

## 9. Handoff format for the next session

**Initial task text:** “Continue AutoRAG Router from GitHub. Read all of `PROJECT_CONTEXT.md`, `AGENTS.md`, `CHANGELOG.md`, `docs/DAILY_LOG.md` and `docs/WORKFLOW.md`; verify current `main`, API tests and Vercel deployment; report actual completed work, outstanding risks and next steps before making changes. After work, prepare changes and request my explicit authorization before any GitHub commit/push.”

**Do not infer:** a successful web demo means Python backend production readiness, routing confidence is calibrated probability, the API uses an LLM, new Vercel deployment follows GitHub pushes, or all research claims are established.

## 2026-10-28 — Research benchmark preparation (owner-authorized source change)

- New independent `benchmarks/` package in the same repository: BEIR and RAGRouter-Bench loaders, toy diagnostic, actual AutoRAGEngine adapter with frozen corpus, fixed BM25/hybrid references, retrieval/routing/lexical answer scores, optional local loopback Qwen/vLLM generation, manifest fingerprints, resume logic, Spark read-only checks and Markdown/JSON reporting.
- Scientific limitation: a lightweight retrieval pilot harness, **NOT** a completed full RAGRouter-Bench competition. No neural dense baseline, full GraphRAG, iterative-RAG parity, real Spark inference, large-corpus acceleration or scientific novelty claim has been established.
- Locally observed (x86_64, CPU; NOT DGX Spark): 24 Python tests passed including 8 new benchmark tests; `compileall`, `node --check`, toy run and report succeeded. Rerun on current GitHub main/CI and on Spark before stating production/research readiness.
- Dataset and model weights must stay local and gitignored. No unattended GitHub commits/pushes or Vercel deployment are authorized. All future remote writes need distinct user approval.
- **For cross-chat memory**, update the owner's ChatGPT Project Sources `PROJECT_MEMORY.md` snapshot (deliver downloadable file for user to add/replace), not an automatic GitHub memory-publishing job.

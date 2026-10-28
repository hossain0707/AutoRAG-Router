# AutoRAG Router — Project Memory — 2026-10-28

**Timezone:** Asia/Seoul (KST, UTC+09:00)  
**Owner:** Md Najmul Hossain  
**Repository:** https://github.com/hossain0707/AutoRAG-Router, branch main  
**Status:** Developer preview, with runnable offline benchmarking harness; no real scientific benchmark or DGX Spark run yet.

This is the first **daily GitHub project memory**, containing a complete current snapshot and individually numbered records of meaningful development changes on this calendar date. Five approved pushes in a day must update this ONE file with five separate entries, not create five new files. Do not treat GitHub documentation as proof of a deployment.

## Current project snapshot

### Product objective
AutoRAG Router is an independent, task-adaptive retrieval framework: interpret the user task; choose retrieval capabilities; retrieve source evidence; report selection reasons and execution trace; optionally fall back to a different strategy when evidence is absent. Its long-term objective is explainable, quality/latency/cost-aware strategy selection and composition. Integration with NEXUS-100 remains optional.

**Current maturity:** v0.1.0 developer preview, not a production-certified, calibrated, or scientifically novel adaptive RAG system. Six routes are implemented as *lightweight patterns*, not full published research systems:
- **No-RAG:** skips document retrieval for trivial dialogue; no full chatbot response.
- **Hybrid:** BM25 + character-trigram fuzzy similarity combined with RRF, **not dense neural embeddings**.
- **Graph:** tagged-entity overlap and one-hop lookup, **not a relational multi-hop knowledge graph**.
- **Agentic-style:** bounded query decomposition, **not an autonomous planning/tool-calling agent**.
- **Multimodal-text:** searches extracted captions, PDF text and tables, **not native visual reasoning**.
- **Structured:** metadata-based lexical/fuzzy search, **not SQL execution or numerical aggregation**.
- **Fallback:** specialized route can retry Hybrid after zero hits; confidence/evidence scores remain heuristics.

### Implementation, files, deployment
- The Python package contains router, retrieval engine, Pydantic contracts, SQLite tenant-partitioned store, FastAPI interface, CLI, local dashboard, tests, Docker and configuration under **autorag/** and root files. The Python system emits extractive hits and traces, not an LLM-composed final answer. Caller-provided tenant IDs are not secure authorization.
- The public demo consists of **docs/index.html**, **docs/app.js** and **docs/styles.css**. It is an independent browser-side JavaScript demo with synthetic records, screenshots, genuine UI-recorded GIF/MP4 and a promotional concept video in **assets/**. The live demo is https://autorag-router-demo.vercel.app/ and does **not** host the Python API, an LLM or a vector database.
- Latest previously verified Vercel state: production READY on 2026-10-27, deployment **dpl_EoAEbCTLC3F5yJg1WWTZ2w6Evuiy**. GitHub pushes do not automatically imply Vercel updates; no Vercel change is part of today's memory-system task.
- Known correctness issue: Structured revenue query retrieved five documents when only the finance source was clearly relevant; unrelated architecture, HR and security passages had misleadingly high displayed relevance. Precision, abstention and score calibration must be fixed.
- Licensing: **AutoRAG Router Personal Noncommercial License v1.0**, copyright Md Najmul Hossain. Personal/noncommercial/educational use subject to license terms; commercial use requires written permission. The current license is source-available, not OSI-approved open source. Historical MIT grants cannot be retroactively revoked.
- Source-of-truth for current behavior is actual code and fresh tests, followed by **PROJECT_CONTEXT.md**, **AGENTS.md**, **CHANGELOG.md**, **docs/WORKFLOW.md**, and this dated history. Historic **docs/DAILY_LOG.md** remains archival, not the new per-change log.

### Existing benchmark program
- The owner-approved benchmark feature is in **benchmarks/**, added in commit **42026e8a0e00826dd098a08433455eb393524408** (2026-10-28 KST), along with a synthetic diagnostic and offline CI smoke test.
- It implements loaders for toy data, BEIR (corpus, queries, qrels), and RAGRouter-Bench (corpus/questions, supporting-fact caution); a real AutoRAGEngine adapter; fixed BM25 and character-trigram Hybrid references; nDCG, Recall, Precision, MRR, lexical EM/F1, p50/p95 retrieval latency; deterministic subsampling, resume fingerprints, JSONL results, Markdown/JSON report; optional loopback-only OpenAI-compatible local vLLM generation.
- Previous test evidence: **24 local Python tests passed** in an x86_64 CPU environment, toy 5 queries × 3 methods = 15 synthetic evaluations, and Python 3.11/3.12 GitHub CI succeeded (run https://github.com/hossain0707/AutoRAG-Router/actions/runs/40540906024). This is NOT external benchmarking evidence.
- Intended research platform: one NVIDIA DGX Spark, 128 GB unified memory, and candidate model **nvidia/Qwen3.8-Flash-Next-FP4-Local**, using NVIDIA's specific Spark-compatible vLLM instructions. **Not yet verified** on the owner's Spark; no weight download, real Qwen inference, BEIR pilot, full RAGRouter-Bench experiment, scientific win or cost advantage is established. True dense neural, GraphRAG and iterative baselines are still outstanding.

### Governance and cross-chat continuity
- Owner instructions: **never automatically commit, push, merge, release or deploy**. Only a particular user-authorized GitHub write is allowed; normal CI and scheduled status reviews are read-only. Do not create a daily auto-commit workflow.
- On each approved source/documentation push, update **project_memory/PROJECT_MEMORY_YYYY-MM-DD.md** for the KST calendar day. Multiple same-day pushes append **Change 03, Change 04, ...** in this same file. Only dated Markdown files belong inside **project_memory/**; never create extra same-date variants, scripts, backups, data or weights there.
- Daily file layout: up-to-date complete project snapshot, outstanding tasks, then individual time-stamped change entries recording added, changed, removed, fixed, tests/evidence, deployment/commit status, decisions, risks and next action. Do not overwrite prior-day memories; note corrections in the current day's file. The first day summarizes older history rather than fabricating files for prior days.
- **scripts/check_project_memory.py** is a read-only CI checker: it uses the HEAD committer date converted to KST; rejects invalid filenames and missing/incomplete daily entries and source pushes without new numbered entries. It does not prove that narrative claims are true. Keep commit time aligned with the KST daily filename.
- This GitHub project_memory directory does **not automatically update ChatGPT Project → Sources**. A separate consolidated Markdown attachment can be manually replaced there; never commit secrets, credentials, private datasets, model weights or raw customer/answer logs.

### Historical milestones (before this daily-memory convention)
- **2026-10-27 KST:** Repo bootstrap; v0.1.0 Python engine/API/tests, Docker, docs, live interactive browser demo, UI GIF and MP4 media, separate Vercel demo, license change to noncommercial, corrected README live link. Original automatic GitHub journal was implemented during continuity work.
- **2026-10-27 KST:** Owner revoked unattended GitHub writes; commit **65113396bcc2755fe3bc5a6167716377e5faaa53** disabled scheduled journal commits/pushes. The daily ChatGPT review is read-only.
- **2026-10-28 KST:** Owner specifically authorized adding the independent benchmarking harness. Commit **42026e8a0e00826dd098a08433455eb393524408** and read-only CI succeeded, without hosting changes.
- **2026-10-28 KST:** Owner approved this one-file-per-day GitHub memory scheme. All older work is retained in handover docs, changelog and Git history; no retrospectively fabricated daily files.

## Outstanding tasks

1. **Correctness first:** fix Structured RAG finance-query precision, irrelevant evidence ranking, abstention and misleading scores; test Python and browser parity.
2. **DGX Spark:** run the read-only Spark device inventory, offline toy diagnostic and report in a clean environment; record verified hardware, actual memory and tests.
3. **External data pilot:** download official BEIR SciFact locally, benchmark BM25, character Hybrid and AutoRAG; avoid data leakage into routing decisions.
4. **Qwen generation:** follow NVIDIA's Spark-specific NVFP4/vLLM recipe, keep the model server loopback-only and run a small common-model answer-generation pilot; do not claim ordinary upstream vLLM works without validation.
5. **Scientific comparators:** add indexed dense retrieval, proper graph/iterative approaches, comparable chunking and context budgets, learned/cost-aware routing policy and oracle reference. RAGRouter-Bench supporting-fact snippet labels may not map to source IDs, so report N/A rather than inventing labels.
6. **Research evidence:** evaluate Recall@k, nDCG, answer correctness/faithfulness, routing regret, p50/p95 latency, tokens and measured cost; multiple seeds, frozen dev/test, statistical intervals and ablations before novelty or superiority claims.
7. **Production hardening:** proper principal-to-tenant authorization, isolation, rate limiting, safe ingestion, injection defenses, reliable deployment parity and observability.
8. **Change documentation:** every future owner-approved push must append a new numbered record to the same KST day's file and update its complete project snapshot; never publish via unattended bots.

## Changes on 2026-10-28 (Asia/Seoul)

### Change 01 — Implement separate benchmark harness in existing repository
- **KST time:** 01:26 KST (GitHub commit timestamp 2026-10-27 16:26 UTC).
- **Task / reason:** Build reproducible benchmark infrastructure without changing the real application or claiming experimental scientific results.
- **Added:** Benchmarks package with loaders, actual engine adapter, fixed lexical baselines, metrics, local Qwen/vLLM client, read-only device checker, report and tests.
- **Changed:** README, agent instructions, changelog, handover, CI offline benchmark smoke test and ignore rules.
- **Removed:** None.
- **Fixed:** Prior absence of a reproducible benchmark runner; Structured retrieval precision bug remains.
- **Tests / evidence:** 24 local Python tests and a 15-evaluation toy run passed; CI Python 3.11 and 3.12 passed at https://github.com/hossain0707/AutoRAG-Router/actions/runs/40540906024. No Spark/Qwen/BEIR results.
- **GitHub / deployment:** Owner-authorized commit 42026e8a0e00826dd098a08433455eb393524408; Vercel unchanged.
- **Decisions:** Keep research experiments modular in the same repo, no paid services required by default, keep unverified qrels as N/A.
- **Risks / blockers:** Full-scale retrieval indexing, genuine neural/graph/iterative competitors and real GPU execution remain outstanding.
- **Next action:** Run Spark device check and toy benchmark, then BEIR pilot.

### Change 02 — Introduce GitHub daily memory convention and CI guard
- **KST time:** 13:33 KST owner approval session; actual committer timestamp may differ.
- **Task / reason:** Preserve complete project state and individually detailed work records, exactly one GitHub memory Markdown file per KST day regardless of multiple pushes.
- **Added:** This dated memory file, read-only memory validation script and regression tests.
- **Changed:** AGENTS.md, CONTRIBUTING.md, docs/WORKFLOW.md, README.md, PROJECT_CONTEXT.md, CHANGELOG.md and read-only GitHub CI.
- **Removed:** None; the existing historical docs/DAILY_LOG.md remains preserved.
- **Fixed:** Ambiguity about daily file duplication, same-day entries and missing documentation on approved pushes.
- **Tests / evidence:** Three checker tests passed locally in a temporary Git repository; GitHub CI pending this new commit and must be verified.
- **GitHub / deployment:** Explicitly authorized one-time source update; exact SHA is available in this file's Git history after commit. No Vercel deployment.
- **Decisions:** One dated file, append another numbered record for every approved push, preserve previous days, and enforce documentation with read-only checks rather than auto-publishing.
- **Risks / blockers:** A format check does not prove narrative accuracy; KST is derived from HEAD commit time; ChatGPT Sources are not auto-synchronized.
- **Next action:** Verify GitHub CI and follow the daily-entry convention on the next explicitly approved task.

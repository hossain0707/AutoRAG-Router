# Agent Instructions — AutoRAG Router

**This is the persistent instruction file for ChatGPT, Codex, AI coding agents and human contributors.** Always read `PROJECT_CONTEXT.md` first, then `README.md`, `CHANGELOG.md`, `docs/DAILY_LOG.md`, `docs/WORKFLOW.md`, `docs/ARCHITECTURE.md`, and inspect current source and remote deployments.

## Mission

Develop an independent, professionally documented **task-adaptive RAG routing framework**, compatible with integration into NEXUS-100, without overstating feature completeness or scientific novelty. User asks for (1) correct production-oriented software, (2) interactive live demo, (3) real screen-recorded README animation and promotional media, (4) individual/noncommercial-only source license with separate permission for commercial use, and (5) durable cross-chat project history.

## Source-of-truth hierarchy

1. Current committed code, actual tests and authenticated cloud provider state are primary for **what currently exists**.
2. `PROJECT_CONTEXT.md` records product intent, decisions, owner-authorized scope and last verified environment state.
3. `CHANGELOG.md` records human interpretation of substantive changes.
4. `docs/DAILY_LOG.md` records mechanically observed Git changes. Auto-generated summaries **do not replace** documentation of design intent.
5. External ChatGPT memory, screenshots, older chat claims or marketing materials may be stale. Reconcile any conflict rather than copying it blindly.

## Owner policy — NO AUTOMATIC GITHUB WRITES (2026-10-27)

**Never commit, push, merge, write GitHub files, publish releases, trigger a write-enabled workflow, or deploy automatically.** The owner requires **explicit approval for each GitHub write**. Read-only scheduled checks and reporting are permitted. Work may be drafted locally, with proposed changes shown to the owner for approval. This policy supersedes previous daily-sync and journal write instructions.

## Non-negotiables

- Never make up capabilities, metrics, benchmark wins, link availability or successful deployments.
- Distinguish browser-only JavaScript static demo from the local Python FastAPI service; the former does **not** host the latter.
- Keep credentials in secure account/CI secret storage. **Never** commit `.env`, API tokens, access keys, SSH keys, cookies, private datasets or personal identifiers.
- Preserve the **Personal Noncommercial License**; no silently changing to MIT/Apache or using the word “open source” as an OSI claim.
- Treat derived source documents as untrusted input; future LLM integration needs prompt-injection defense.
- Do not deploy changes that require payment or new infrastructure subscriptions without approval.
- Respect user intent and avoid destructive changes unless explicitly authorized.
- With substantial edits: run `python -m pytest -q`, `python -m compileall -q autorag`, `node --check docs/app.js` when available; report exactly what was executed.
- For demo changes: run or inspect a live browser flow and check source/hosting parity. Do not equate GitHub push with Vercel rollout.

## Definition of done — for **every** meaningful change

1. Review current repository, open issues and last daily journal entry.
2. Make a focused change and test; cite measured evidence and known limitations.
3. Update `PROJECT_CONTEXT.md` if architecture, deployed state, risk, next action or key design decision changed.
4. Update `CHANGELOG.md` for feature, security, interface, licensing, workflow or deployment changes. Mark removed functionality explicitly.
5. Prepare related code + documentation together, but **do not commit or push without explicit user authorization for the specific change**. The historical `docs/DAILY_LOG.md` is no longer auto-committed.
6. Only if the owner approves a GitHub write: commit, then verify the resulting commit URL, CI and any production URL; never assume green status.
7. Leave a clear next-step handover suitable for a completely new chat without prior messages; report proposed source changes without writing remotely unless approved.

## Reviewer checklist for next chat

- Which commit on `main` is current? What changed since the last journal cursor?
- Is `https://autorag-router-demo.vercel.app/` reachable and functional? Is its JavaScript current with `docs/app.js`?
- Did the Python tests pass on the current revision? What failed or was skipped?
- Has Structured RAG precision improved? Previously irrelevant documents were returned with high scores.
- Have metadata/schema and tenant auth/security controls changed?
- Is the license still personal-noncommercial? Are commercial permissions documented separately?
- Is the latest change recorded in `PROJECT_CONTEXT.md`, `CHANGELOG.md` and, if manually approved, `docs/DAILY_LOG.md`?

## How to continue

In a new session: **“Read the complete `PROJECT_CONTEXT.md`, `AGENTS.md`, `CHANGELOG.md`, `docs/DAILY_LOG.md`, and `docs/WORKFLOW.md` on `hossain0707/AutoRAG-Router`. Then inspect fresh GitHub and Vercel state. Continue the next priority without losing implementation details; after completing work, draft changes to these Markdown files; never commit or push without my explicit approval.”**

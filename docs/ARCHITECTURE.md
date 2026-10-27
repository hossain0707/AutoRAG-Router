# Architecture and routing contract

## Execution path

1. Validate and authorize requests. Requests include a tenant identifier; **the caller-provided tenant is not an authenticated identity** in this version.
2. Rule-based, explainable route assigns one of `no_rag`, `hybrid`, `graph`, `agentic`, `multimodal`, `structured`.
3. Execute local retrieval over tenant-partitioned documents. Filter metadata before retrieval, cap stored search to 2,000 records per tenant and response hits to 20.
4. If a specialized route returns no results, attempt hybrid retrieval.
5. Emit extractive snippets only; include source identifiers, evidence status, strategy trace and latency.

## Routing details

| Route | Implemented behavior | Upgrade path |
| --- | --- | --- |
| No-RAG | Skip retrieval for simple social tasks | Connect an LLM/chat provider |
| Hybrid | BM25 + character-trigram cosine with RRF | Vector DB + neural embeddings + cross-encoder |
| Graph | Tag-index based one-hop entity overlap | Neo4j and multi-hop reasoning |
| Agentic | Bounded decomposition over `and`, `vs`, `?` | Tool-using planning agent with budgets |
| Multimodal | Retrieval over already extracted PDF/image/table text | OCR and vision encoders at ingestion |
| Structured | Deterministic metadata filter and hybrid retrieval | Whitelisted SQL planner and warehouse |
| Corrective | Empty specialized retrieval triggers hybrid | Evidence graders and iterative recovery |
| Self-RAG-style | Evidence presence/score check | Calibrated attribution and claim verification |

**Important:** These capabilities are deliberately not described as a fully trained router, full GraphRAG, multimodal image understanding, or LLM-powered autonomous agents. They are a tested composable baseline. The default character-trigram retrieval approximates fuzzy lexical similarity, not neural semantic similarity.

## Threat model and release limitations

- API-key header checks can protect a single API deployment, but do not identify individual users/tenants. Put the service behind an identity-aware gateway and bind tenant IDs to authenticated principals before multi-tenant Internet exposure.
- API docs and dashboard are intentionally public even when API-key mode is active; dashboard submits an optional key. Use a gateway to restrict pages if required.
- API has bounded input sizes but **no built-in rate limiter**. Add reverse-proxy rate limits, request-body limits, TLS, audit logs and telemetry before Internet exposure.
- SQLite WAL is suitable for a single-instance local deployment. Introduce a transactional multi-replica data layer for horizontal scaling.
- Scoring threshold is a heuristic, not a calibrated correctness measure; retrieval snippets may be relevant without supporting the answer. Do not use this evidence indicator as proof.
- Ingestion text is untrusted. Don't insert it into privileged system prompts when adding an LLM; protect against retrieval prompt injection.
- No telemetry exports, no model downloads, and no external requests by default.

## Roadmap for enterprise use

- AuthN/AuthZ with identity-derived tenant selection; audit events; rate limits; quotas.
- Real neural embedding adapters; vector indexing; neural rerankers; chunking and incremental indexing.
- Graph storage/traversal with entity resolution; versioned provenance and time-aware edges.
- Vision/OCR and parsing plugins for PDFs, tables, scanned documents and images.
- Calibrated retrieval quality/evidence grader, routing cost optimization, online/offline learning.
- Generation connectors with source-grounding and benchmarked faithfulness.
- Persistent metrics and OpenTelemetry traces; distributed workload support.

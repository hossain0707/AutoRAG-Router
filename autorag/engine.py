"""Composed routing, retrieval, verification, fallback and extractive grounded response."""
from __future__ import annotations

import re
import time
import uuid
from .models import QueryRequest, QueryResponse, Hit
from .retrieval import ranked_hybrid, ranked_agentic, ranked_graph, ranked_structured
from .router import route
from .store import SQLiteStore


class AutoRAGEngine:
    def __init__(self, store: SQLiteStore):
        self.store = store

    def query(self, request: QueryRequest) -> QueryResponse:
        started = time.perf_counter()
        decision = route(request)
        trace = ["policy:" + decision.primary]
        if decision.primary == "no_rag":
            return self._response("No retrieval required for this conversational request.", False,
                                  decision, [], trace, started)
        docs = self.store.list(request.tenant_id)
        if not docs:
            return self._response("No documents are indexed for this tenant. Ingest documents first.",
                                  False, decision, [], trace + ["empty_index"], started)
        if request.filters:
            docs = [d for d in docs if all(d.metadata.get(k) == v for k, v in request.filters.items())]
            trace.append("metadata_filter")
        if decision.primary == "graph":
            ranked = ranked_graph(request.query, docs, request.top_k)
        elif decision.primary == "agentic":
            ranked = ranked_agentic(request.query, docs, request.top_k)
        elif decision.primary == "structured":
            ranked = ranked_structured(request.query, docs, request.top_k, request.filters)
        elif decision.primary == "multimodal":
            converted = [d for d in docs if d.kind in ("image_caption", "pdf_text", "table")]
            ranked = ranked_hybrid(request.query, converted, request.top_k)
            trace.append("pre_extracted_multimodal_text_only")
        else:
            ranked = ranked_hybrid(request.query, docs, request.top_k)
        trace.append("retrieved:" + str(len(ranked)))
        if not ranked and "hybrid_fallback" in decision.stages:
            ranked = ranked_hybrid(request.query, docs, request.top_k)
            trace.append("hybrid_fallback_triggered")
        hits = [Hit(document_id=d.id, title=d.title, source=d.source,
                    snippet=self._snippet(d.text, request.query), score=score, method=method)
                for d, score, method in ranked]
        # A hit is retrieval evidence, not a guarantee that it answers the question.
        grounded = bool(hits and hits[0].score >= 0.05)
        if request.verify:
            trace.append("evidence_check:" + ("pass" if grounded else "insufficient"))
        if grounded:
            answer = "Relevant indexed evidence (extractive; no generative model configured):\n" + "\n".join(
                f"[{i}] {h.snippet} (source: {h.source})" for i, h in enumerate(hits[:3], 1))
        else:
            answer = "Insufficient matching evidence in the indexed documents; no factual answer generated."
        return self._response(answer, grounded, decision, hits, trace, started)

    @staticmethod
    def _snippet(text: str, query: str) -> str:
        qterms = set(re.findall(r"\w+", query.casefold()))
        sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
        best = max(sentences, key=lambda s: len(qterms & set(re.findall(r"\w+", s.casefold()))),
                   default=text)
        return best[:420]

    @staticmethod
    def _response(answer, grounded, decision, hits, trace, started) -> QueryResponse:
        return QueryResponse(answer=answer, grounded=grounded, decision=decision, hits=hits,
                             trace=trace, latency_ms=round((time.perf_counter() - started)*1000, 2),
                             request_id=uuid.uuid4().hex)

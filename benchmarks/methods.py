"""Adapters that execute the repository's actual retrieval/engine functions.

Names deliberately distinguish this lightweight router's implementations from
research-grade GraphRAG, dense embedding retrieval and iterative RAG.
"""
from __future__ import annotations

from collections.abc import Sequence

from autorag.engine import AutoRAGEngine
from autorag.models import Document, QueryRequest
from autorag.retrieval import bm25, ranked_hybrid
from .schema import RetrievalResult, Retrieved

METHODS = ("bm25", "hybrid_char3", "autorag_auto", "autorag_graph_tagged",
           "autorag_agentic_decomposition", "autorag_structured_metadata",
           "autorag_multimodal_text", "no_retrieval")
OVERRIDES = {"autorag_graph_tagged": "graph", "autorag_agentic_decomposition": "agentic",
             "autorag_structured_metadata": "structured", "autorag_multimodal_text": "multimodal"}


class _FrozenStore:
    """Inject entire immutable benchmark corpus into actual AutoRAGEngine.

    Avoids SQLiteStore.list's 2000-document cap; does NOT change the engine.
    Baseline operates on the exact same corpus in memory as other baselines.
    """
    def __init__(self, docs: Sequence[Document]) -> None:
        self.docs = list(docs)

    def list(self, tenant_id: str) -> list[Document]:
        if tenant_id != "benchmark":
            return []
        return self.docs


class BenchMethods:
    def __init__(self, documents: list[Document], parents: dict[str, str], top_k: int):
        if not 1 <= top_k <= 20:
            raise ValueError("top_k must be 1..20")
        self.docs = documents
        self.parents = parents
        self.top_k = top_k
        self.engine = AutoRAGEngine(_FrozenStore(documents))

    def _unique(self, raw: list[tuple[str, float, str]]) -> list[Retrieved]:
        result: list[Retrieved] = []
        seen: set[str] = set()
        for chunk_id, score, method in raw:
            parent = self.parents[chunk_id]
            if parent not in seen:
                seen.add(parent)
                result.append(Retrieved(doc_id=parent, score=float(score), method=method))
            if len(result) >= self.top_k:
                break
        return result

    def retrieve(self, method: str, query: str) -> RetrievalResult:
        if method not in METHODS:
            raise ValueError(f"Unknown method {method!r}; allowed: {METHODS}")
        if method == "no_retrieval":
            return RetrievalResult("no_rag", [], ["explicit_no_retrieval_baseline"])
        # Ask for enough chunks to deduplicate by original source ID; no qrels
        # are consulted. Core engine has a top_k<=20 public API bound.
        candidate_k = 20
        if method == "bm25":
            scores = bm25(query, self.docs)
            ranked = sorted(((key, value) for key, value in scores.items() if value > 0),
                            key=lambda p: (-p[1], p[0]))[:candidate_k]
            return RetrievalResult("bm25", self._unique([(i, s, "bm25") for i, s in ranked]))
        if method == "hybrid_char3":
            ranked = ranked_hybrid(query, self.docs, candidate_k)
            return RetrievalResult("hybrid", self._unique([(d.id, s, m) for d, s, m in ranked]))
        mode = OVERRIDES.get(method, "auto")
        resp = self.engine.query(QueryRequest(query=query, tenant_id="benchmark",
                                              mode=mode, top_k=candidate_k))
        return RetrievalResult(resp.decision.primary,
                               self._unique([(h.document_id, h.score, h.method) for h in resp.hits]),
                               resp.trace)

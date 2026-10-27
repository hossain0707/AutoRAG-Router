"""Explainable, bounded-cost routing policy. Replaceable with a learned policy later."""
from __future__ import annotations

import re
from .models import QueryRequest, RoutingDecision

RELATIONS = ("relationship", "related", "connected", "connect", "dependency", "dependencies", "depends", "network", "graph", "between", "linked")
COMPLEX = ("compare", "analyze", "investigate", "research", "synthesize", "across", "multi-step", "multiple", "evaluate", "why")
VISUAL = ("diagram", "image", "screenshot", "figure", "chart", "photo", "pdf", "table in the")
STRUCTURED = ("sum", "total", "average", "count", "revenue", "sales", "records", "rows", "group by", "how many")
NO_RETRIEVAL = ("hello", "hi", "thanks", "thank you", "write a poem", "tell a joke")


def contains_any(query: str, tokens: tuple[str, ...]) -> bool:
    return any(re.search(r"\b" + re.escape(token) + r"\b", query) for token in tokens)


def route(request: QueryRequest) -> RoutingDecision:
    if request.mode != "auto":
        return RoutingDecision(primary=request.mode, stages=[request.mode], confidence=1,
                               reasons=["Explicit strategy override requested"])
    q = request.query.lower().strip()
    if q in NO_RETRIEVAL or contains_any(q, NO_RETRIEVAL[:2]) and len(q) < 18:
        primary, confidence, reason = "no_rag", .98, "Conversation does not require document lookup"
    elif contains_any(q, VISUAL):
        primary, confidence, reason = "multimodal", .85, "Visual/document-derived information requested"
    elif contains_any(q, STRUCTURED):
        primary, confidence, reason = "structured", .80, "Quantitative or structured-record intent"
    elif contains_any(q, RELATIONS):
        primary, confidence, reason = "graph", .82, "Entity relationship intent"
    elif contains_any(q, COMPLEX) or len(q.split()) >= 32:
        primary, confidence, reason = "agentic", .79, "Complex or multi-part information need"
    else:
        primary, confidence, reason = "hybrid", .76, "General factual retrieval benefits from lexical and dense signals"
    stages = [primary]
    if primary not in ("no_rag", "hybrid"):
        stages.append("hybrid_fallback")
    if request.verify and primary != "no_rag":
        stages.append("evidence_check")
    return RoutingDecision(primary=primary, stages=stages, confidence=confidence,
                           reasons=[reason], estimated_cost="local")

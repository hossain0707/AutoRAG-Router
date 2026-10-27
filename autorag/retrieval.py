"""Runnable offline retrieval primitives. Dense means hashed character features, not neural embeddings.

Production plugins may replace `char_similarity` with an embedding provider and reranker.
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from .models import Document


def tokens(text: str) -> list[str]:
    return re.findall(r"[\w]+", text.casefold())


def bm25(query: str, docs: list[Document]) -> dict[str, float]:
    if not docs:
        return {}
    q = set(tokens(query))
    lengths = [len(tokens(d.text + " " + d.title)) for d in docs]
    avgdl = sum(lengths) / max(len(lengths), 1)
    df = Counter(t for d in docs for t in set(tokens(d.text + " " + d.title)))
    out: dict[str, float] = {}
    for d, length in zip(docs, lengths):
        tf = Counter(tokens(d.text + " " + d.title))
        score = 0.0
        for t in q:
            if not tf[t]:
                continue
            idf = math.log(1 + (len(docs) - df[t] + 0.5) / (df[t] + 0.5))
            score += idf * tf[t] * 2.2 / (tf[t] + 1.2 * (0.25 + 0.75 * length / max(avgdl, 1)))
        out[d.id] = score
    return out


def ngrams(text: str) -> Counter[str]:
    normalized = " ".join(tokens(text))
    return Counter(normalized[i:i+3] for i in range(max(0, len(normalized) - 2)))


def char_similarity(query: str, text: str) -> float:
    a, b = ngrams(query), ngrams(text)
    if not a or not b:
        return 0.0
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    return dot / (math.sqrt(sum(v*v for v in a.values())) * math.sqrt(sum(v*v for v in b.values())))


def ranked_hybrid(query: str, docs: list[Document], top_k: int) -> list[tuple[Document, float, str]]:
    """Reciprocal rank fusion (k=60). Excludes zero-evidence documents."""
    lexical = bm25(query, docs)
    dense = {d.id: char_similarity(query, d.title + " " + d.text) for d in docs}
    positions = defaultdict(float)
    for scores in (lexical, dense):
        ordered = sorted(((i, s) for i, s in scores.items() if s > 0), key=lambda p: (-p[1], p[0]))
        for rank, (doc_id, _) in enumerate(ordered, 1):
            positions[doc_id] += 1 / (60 + rank)
    return [(d, round(positions[d.id] / (2 / 61), 4), "hybrid_bm25_char3_rrf")
            for d in sorted(docs, key=lambda d: (-positions[d.id], d.id))
            if positions[d.id] > 0][:top_k]


def ranked_graph(query: str, docs: list[Document], top_k: int) -> list[tuple[Document, float, str]]:
    """One-hop entity-overlap traversal using explicitly ingested entity tags."""
    terms = set(tokens(query))
    seeds = {e.casefold() for d in docs for e in d.entities if e.casefold() in terms
             or any(e.casefold() in query.casefold() for _ in [0])}
    if not seeds:
        return []
    matches = [(d, len({e.casefold() for e in d.entities} & seeds) / max(len(seeds), 1), "entity_graph")
               for d in docs if set(e.casefold() for e in d.entities) & seeds]
    return sorted(matches, key=lambda x: (-x[1], x[0].id))[:top_k]


def ranked_structured(query: str, docs: list[Document], top_k: int,
                      filters: dict) -> list[tuple[Document, float, str]]:
    eligible = [d for d in docs if all(d.metadata.get(k) == v for k, v in filters.items())]
    if not eligible:
        return []
    return [(d, s, "structured_filter+" + name)
            for d, s, name in ranked_hybrid(query, eligible, top_k)]


def ranked_agentic(query: str, docs: list[Document], top_k: int) -> list[tuple[Document, float, str]]:
    """Bounded query decomposition; not an autonomous web-searching agent."""
    parts = [p.strip() for p in re.split(r"\b(?:and|versus|vs\.?|compared to)\b|[;?]", query, flags=re.I)
             if len(p.strip()) >= 3][:4]
    if not parts:
        parts = [query]
    aggregate: dict[str, float] = defaultdict(float)
    for part in parts:
        for d, score, _ in ranked_hybrid(part, docs, min(20, len(docs))):
            aggregate[d.id] = max(aggregate[d.id], score)
    return [(d, round(aggregate[d.id], 4), "decomposed_hybrid")
            for d in sorted(docs, key=lambda d: (-aggregate[d.id], d.id)) if aggregate[d.id] > 0][:top_k]

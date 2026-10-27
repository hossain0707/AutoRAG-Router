"""Transparent rank-based metrics and conservative lexical answer metrics.

No LLM judge, semantic correctness or faithfulness is inferred by these functions.
"""
from __future__ import annotations

from collections import Counter
import math
import re


def retrieval_scores(doc_ids: list[str], relevant: dict[str, float] | None,
                     k: int) -> dict[str, float | None]:
    missing = {"ndcg_at_k": None, "recall_at_k": None,
               "precision_at_k": None, "mrr_at_k": None}
    if relevant is None or not any(v > 0 for v in relevant.values()):
        return missing
    ranked = list(dict.fromkeys(doc_ids))[:k]
    positives = {doc_id for doc_id, v in relevant.items() if v > 0}
    hits = sum(doc_id in positives for doc_id in ranked)
    dcg = sum((2 ** relevant.get(doc_id, 0) - 1) / math.log2(rank + 2)
              for rank, doc_id in enumerate(ranked))
    ideal = sorted((value for value in relevant.values() if value > 0), reverse=True)[:k]
    idcg = sum((2 ** value - 1) / math.log2(rank + 2)
               for rank, value in enumerate(ideal))
    first_rank = next((rank for rank, doc_id in enumerate(ranked, 1) if doc_id in positives), None)
    return {"ndcg_at_k": dcg / idcg if idcg else None,
            "recall_at_k": hits / len(positives),
            "precision_at_k": hits / k,
            "mrr_at_k": 1.0 / first_rank if first_rank is not None else 0.0}


def normalize(text: str) -> list[str]:
    lowered = text.casefold()
    lowered = re.sub(r"[^\w\s]", " ", lowered)
    return lowered.split()


def answer_scores(prediction: str, reference: str | None) -> dict[str, float | None]:
    if reference is None or not reference.strip():
        return {"exact_match": None, "token_f1": None}
    p, r = normalize(prediction), normalize(reference)
    em = float(p == r)
    common = sum((Counter(p) & Counter(r)).values())
    f1 = 2 * common / (len(p) + len(r)) if p or r else 1.0
    return {"exact_match": em, "token_f1": f1}

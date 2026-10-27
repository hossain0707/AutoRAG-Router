"""Benchmark schema, intentionally separate from the public API contracts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from autorag.models import Document


@dataclass(frozen=True)
class Case:
    case_id: str
    query: str
    # None means retrieval ground truth is unknown; {} means explicitly no positives.
    relevant: dict[str, float] | None = None
    answer: str | None = None
    expected_route: str | None = None
    query_type: str | None = None

    def __post_init__(self) -> None:
        if not self.case_id or not self.query.strip():
            raise ValueError("A benchmark case requires an id and a nonempty query")
        if self.relevant is not None and any(x < 0 for x in self.relevant.values()):
            raise ValueError("Relevance grades must be non-negative")


@dataclass
class Dataset:
    name: str
    documents: list[Document]
    cases: list[Case]
    # Maps chunk id -> ORIGINAL source id, so qrels are evaluated against parent ids.
    parents: dict[str, str]
    warnings: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        ids = [d.id for d in self.documents]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate indexed document/chunk IDs")
        if set(ids) != set(self.parents):
            raise ValueError("Every indexed chunk must have a parent source ID")
        cases = [c.case_id for c in self.cases]
        if len(cases) != len(set(cases)):
            raise ValueError("Duplicate benchmark query IDs")
        if not ids or not cases:
            raise ValueError("Dataset must include documents and queries")
        originals = set(self.parents.values())
        for c in self.cases:
            if c.relevant is not None:
                unknown = {r for r in c.relevant if r not in originals}
                if unknown:
                    raise ValueError(f"Unknown source IDs in qrels for {c.case_id}: {sorted(unknown)[:4]}")


@dataclass(frozen=True)
class Retrieved:
    doc_id: str
    score: float
    method: str


@dataclass
class RetrievalResult:
    selected_route: str
    hits: list[Retrieved]
    trace: list[str] = field(default_factory=list)

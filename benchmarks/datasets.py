"""Deterministic adapters for toy, BEIR and RAGRouter-Bench data.

Never infer relevance from the question or search results: missing ground truth
is explicit and is never silently counted as zero quality.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from autorag.models import Document
from .schema import Case, Dataset


def _rows(path: Path) -> Iterable[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.suffix == ".jsonl":
        with path.open(encoding="utf-8") as stream:
            for lineno, line in enumerate(stream, 1):
                if line.strip():
                    item = json.loads(line)
                    if not isinstance(item, dict):
                        raise ValueError(f"Expected object in {path}:{lineno}")
                    yield item
    elif path.suffix == ".json":
        content = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(content, list):
            raise ValueError(f"Expected JSON array in {path}")
        for item in content:
            if not isinstance(item, dict):
                raise ValueError(f"Expected object in {path}")
            yield item
    else:
        raise ValueError(f"Unsupported file format: {path}")


def _field(item: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in item and item[name] is not None:
            return item[name]
    return None


def _source_id(item: dict[str, Any], *, question: bool = False) -> str:
    keys = ("question_id", "_id", "id") if question else ("doc_id", "_id", "id")
    ident = _field(item, *keys)
    if ident is None or str(ident) == "":
        raise ValueError(f"Missing source identifier; accepted fields: {keys}")
    return str(ident)


def _pack(name: str, docs_raw: Iterable[dict[str, Any]], cases: list[Case],
          *, chunk_chars: int = 3000, overlap: int = 250, warnings: list[str] | None = None,
          meta: dict[str, Any] | None = None) -> Dataset:
    if not 300 <= chunk_chars <= 50000 or not 0 <= overlap < chunk_chars:
        raise ValueError("chunk_chars must be 300..50000 and overlap smaller than chunk")
    docs: list[Document] = []
    parents: dict[str, str] = {}
    original_ids: set[str] = set()
    for item in docs_raw:
        origin = _source_id(item)
        if origin in original_ids:
            raise ValueError(f"Repeated source id: {origin}")
        original_ids.add(origin)
        title = str(_field(item, "title") or "Untitled")[:256]
        text = _field(item, "text", "context", "contents")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"Missing nonempty text/context for source {origin}")
        # Stable internal ids are bounded and safe under Document's strict API pattern.
        hashed = hashlib.sha256((name + "\0" + origin).encode()).hexdigest()[:24]
        for index, start in enumerate(range(0, len(text), chunk_chars - overlap)):
            part = text[start:start + chunk_chars]
            if not part:
                break
            # Avoid near-empty trailing duplicate chunks entirely contained in previous one.
            if index and len(part) <= overlap:
                break
            chunk_id = f"b{hashed}_{index:05d}"
            docs.append(Document(id=chunk_id, title=title, text=part, tenant_id="benchmark",
                                 source=name, kind="text", metadata={"original_id": origin}))
            parents[chunk_id] = origin
    dataset = Dataset(name=name, documents=docs, cases=cases, parents=parents,
                      warnings=warnings or [], meta=meta or {})
    dataset.validate()
    return dataset


def load_beir(root: Path, *, split: str = "test", chunk_chars: int = 3000,
              overlap: int = 250) -> Dataset:
    root = Path(root)
    if not split.replace("_", "").isalnum():
        raise ValueError("Invalid BEIR split")
    corpus_path, query_path = root / "corpus.jsonl", root / "queries.jsonl"
    qrels_path = root / "qrels" / f"{split}.tsv"
    qrels: dict[str, dict[str, float]] = {}
    if not qrels_path.is_file():
        raise FileNotFoundError(f"BEIR qrels for requested split not found: {qrels_path}")
    with qrels_path.open(encoding="utf-8", newline="") as stream:
        table = csv.DictReader(stream, delimiter="\t")
        headers = table.fieldnames or []
        # Official BEIR header: query-id, corpus-id, score
        for required in ("query-id", "corpus-id", "score"):
            if required not in headers:
                raise ValueError(f"Invalid BEIR qrels header (missing {required})")
        for row in table:
            grade = float(row["score"])
            if grade < 0:
                raise ValueError("Negative relevance grade")
            if grade > 0:
                qrels.setdefault(row["query-id"], {})[row["corpus-id"]] = grade
    cases = [Case(case_id=_source_id(item, question=True), query=str(_field(item, "text", "question") or ""),
                  relevant=qrels[_source_id(item, question=True)])
             for item in _rows(query_path) if _source_id(item, question=True) in qrels]
    if not cases:
        raise ValueError("BEIR split has no matching queries and positive qrels")
    return _pack(f"beir:{root.name}:{split}", _rows(corpus_path), cases,
                 chunk_chars=chunk_chars, overlap=overlap,
                 meta={"format": "beir", "split": split,
                       "source_paths": [str(corpus_path), str(query_path), str(qrels_path)]})


def load_ragrouter(root: Path, *, chunk_chars: int = 3000, overlap: int = 250) -> Dataset:
    root = Path(root)
    docs_path, cases_path = root / "Corpus.json", root / "Question.json"
    # A supporting fact can be an ID or a literal evidence string. Only IDs are
    # acceptable qrels; literal strings cannot establish document relevance.
    raw_docs = list(_rows(docs_path))
    originals = {_source_id(d) for d in raw_docs}
    cases: list[Case] = []
    unresolved = 0
    for item in _rows(cases_path):
        facts = _field(item, "supporting_facts")
        relevant = None
        if isinstance(facts, list) and facts:
            ids = [str(f) for f in facts if isinstance(f, (str, int))]
            if len(ids) == len(facts) and all(f in originals for f in ids):
                relevant = {f: 1.0 for f in ids}
        if relevant is None:
            unresolved += 1
        answer = _field(item, "answer", "reference_answer")
        if isinstance(answer, list):
            answer = " | ".join(str(x) for x in answer)
        cases.append(Case(case_id=_source_id(item, question=True),
                          query=str(_field(item, "question", "query") or ""),
                          answer=str(answer) if answer is not None else None,
                          relevant=relevant,
                          query_type=str(_field(item, "query_type", "type") or "unknown")))
    warns = []
    if unresolved:
        warns.append(f"{unresolved}/{len(cases)} queries lack resolvable document-ID supporting facts; retrieval metrics N/A for those queries. Query type is NOT a gold RAG strategy label.")
    return _pack(f"ragrouter:{root.name}", raw_docs, cases, chunk_chars=chunk_chars,
                 overlap=overlap, warnings=warns,
                 meta={"format": "ragrouter", "split": "unassigned (define split before learned routing)",
                       "source_paths": [str(docs_path), str(cases_path)]})


def toy_dataset() -> Dataset:
    docs = [
        {"doc_id": "atlas", "title": "Atlas ingestion", "text": "Atlas ingests events and transfers them to Beacon for indexing."},
        {"doc_id": "beacon", "title": "Beacon search", "text": "Beacon indexes incoming events from Atlas and enables keyword search."},
        {"doc_id": "revenue", "title": "Quarterly financials", "text": "Total Q2 2026 revenue was 720000 USD."},
        {"doc_id": "leave", "title": "Employee leave policy", "text": "Employees receive twenty paid leave days per year."},
        {"doc_id": "security", "title": "Security incident policy", "text": "Report phishing and credential theft to security within one hour."},
        {"doc_id": "diagram", "title": "Architecture diagram caption", "text": "Service diagram shows Atlas writes to Beacon index."},
    ]
    cases = [
        Case("graph01", "How is Atlas connected to Beacon?", {"atlas": 1, "beacon": 1}, expected_route="graph"),
        Case("struct01", "What was the Q2 2026 revenue total?", {"revenue": 1}, answer="720000 USD", expected_route="structured"),
        Case("policy01", "What is the employee paid leave policy?", {"leave": 1}, answer="twenty paid leave days", expected_route="hybrid"),
        Case("security01", "How should phishing be reported?", {"security": 1}, expected_route="hybrid"),
        Case("chat01", "Hello", {}, expected_route="no_rag"),
    ]
    return _pack("toy-diagnostic", docs, cases, meta={"format": "toy", "synthetic": True, "split": "diagnostic_only"})


def load_dataset(kind: str, root: Path | None, split: str,
                 chunk_chars: int, overlap: int) -> Dataset:
    if kind == "toy":
        return toy_dataset()
    if root is None:
        raise ValueError(f"--data-root is required for {kind}")
    if kind == "beir":
        return load_beir(root, split=split, chunk_chars=chunk_chars, overlap=overlap)
    if kind == "ragrouter":
        return load_ragrouter(root, chunk_chars=chunk_chars, overlap=overlap)
    raise ValueError(f"Unknown dataset format: {kind}")

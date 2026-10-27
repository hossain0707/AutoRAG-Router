"""Run offline, reproducible, append-only RAG retrieval evaluations.

Run locally: python -m benchmarks.run --dataset toy --out /tmp/autorag-toy
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys
import time
from typing import Any

from .datasets import load_dataset
from .generation import LocalChatClient
from .methods import METHODS, BenchMethods
from .metrics import answer_scores, retrieval_scores
from .schema import Case, Dataset


def _digest(data: Dataset, selected: list[Case], methods: list[str], args: argparse.Namespace) -> str:
    hasher = hashlib.sha256()
    for doc in data.documents:
        hasher.update(json.dumps([doc.id, doc.title, doc.text, data.parents[doc.id]],
                                 ensure_ascii=False).encode("utf-8"))
        hasher.update(b"\n")
    for c in selected:
        hasher.update(json.dumps([c.case_id, c.query, c.relevant, c.answer, c.expected_route],
                                 sort_keys=True, ensure_ascii=False).encode("utf-8"))
        hasher.update(b"\n")
    params = [methods, args.top_k, args.generate, args.model if args.generate else None,
              args.endpoint if args.generate else None, args.max_output_tokens,
              args.chunk_chars, args.overlap, args.seed]
    hasher.update(json.dumps(params, sort_keys=True).encode("utf-8"))
    # Detect changes to retrieval, router, generation, schema, and metric logic.
    root = Path(__file__).resolve().parent.parent
    for source in ("autorag/engine.py", "autorag/router.py", "autorag/retrieval.py",
                   "benchmarks/run.py", "benchmarks/datasets.py", "benchmarks/methods.py",
                   "benchmarks/metrics.py", "benchmarks/generation.py"):
        hasher.update((root / source).read_bytes())
    return hasher.hexdigest()


def _get_sha() -> str | None:
    try:
        root = Path(__file__).resolve().parent.parent
        cp = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True,
                            text=True, timeout=4, check=True)
        return cp.stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None


def _safe_write(path: Path, data: dict[str, Any]) -> None:
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def _selected(dataset: Dataset, limit: int | None, seed: int) -> list[Case]:
    ordered = sorted(dataset.cases, key=lambda c: c.case_id)
    if limit is None:
        return ordered
    if limit <= 0:
        raise ValueError("--limit-queries must be positive")
    rng = random.Random(seed)
    return sorted(rng.sample(ordered, min(limit, len(ordered))), key=lambda c: c.case_id)


def run(args: argparse.Namespace) -> dict[str, Any]:
    methods = [m.strip() for m in args.methods.split(",") if m.strip()]
    if not methods or len(set(methods)) != len(methods) or any(m not in METHODS for m in methods):
        raise ValueError(f"--methods must be unique members of: {', '.join(METHODS)}")
    if not 1 <= args.top_k <= 20:
        raise ValueError("--top-k must be between 1 and 20")
    if args.generate and (not args.model or not args.endpoint):
        raise ValueError("--generate requires --model and --endpoint")
    if not args.generate and (args.model or args.endpoint):
        raise ValueError("--model and --endpoint require --generate to avoid accidental LLM use")
    # Reject external targets BEFORE dataset IO or creating a results folder.
    client = LocalChatClient(args.endpoint, args.model,
                             max_output_tokens=args.max_output_tokens) if args.generate else None
    dataset = load_dataset(args.dataset, args.data_root, args.split,
                           args.chunk_chars, args.overlap)
    selected = _selected(dataset, args.limit_queries, args.seed)
    signature = _digest(dataset, selected, methods, args)
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    manifest_file, results_file = out / "manifest.json", out / "results.jsonl"
    manifest: dict[str, Any] = {
        "schema_version": "0.1", "signature": signature,
        "dataset": dataset.name, "dataset_meta": dataset.meta,
        "warnings": dataset.warnings,
        "dataset_original_documents": len(set(dataset.parents.values())),
        "indexed_chunks": len(dataset.documents),
        "selected_queries": len(selected), "total_queries": len(dataset.cases),
        "methods": methods, "top_k": args.top_k, "seed": args.seed,
        "generation_enabled": args.generate,
        "model": args.model if args.generate else None,
        "model_endpoint": args.endpoint if args.generate else None,
        "max_output_tokens": args.max_output_tokens if args.generate else None,
        "source_git_sha": _get_sha(),
        "limitations": [
            "No learned routing or production-scale index; reference engine may be slow on large corpora.",
            "Graph route is tag overlap; Agentic is bounded decomposition; Hybrid has no neural vectors.",
            "Query types in RAGRouter-Bench are NOT supervised strategy labels.",
            "Exact-match/token F1 are lexical metrics; NOT semantic correctness or factual faithfulness.",
            "No metric is comparable to published SOTA without matching splits, models and preprocessing.",
        ],
    }
    done: set[tuple[str, str]] = set()
    if manifest_file.exists() or results_file.exists():
        if not args.resume or not manifest_file.exists() or not results_file.exists():
            raise FileExistsError("Run directory contains results; use --resume or a new --out directory")
        earlier = json.loads(manifest_file.read_text(encoding="utf-8"))
        if earlier.get("signature") != signature:
            raise ValueError("Cannot resume: dataset, code, model or evaluation configuration changed")
        for lineno, line in enumerate(results_file.read_text(encoding="utf-8").splitlines(), 1):
            try:
                row = json.loads(line)
                key = (row["case_id"], row["method"])
            except (ValueError, KeyError) as e:
                raise ValueError(f"Invalid previous results on line {lineno}: {e}") from e
            if key in done:
                raise ValueError(f"Duplicate previous result for {key}")
            done.add(key)
    else:
        _safe_write(manifest_file, manifest)
        results_file.touch()
    adapters = BenchMethods(dataset.documents, dataset.parents, args.top_k)
    samples = 0
    with results_file.open("a", encoding="utf-8", buffering=1) as stream:
        for case in selected:
            for method in methods:
                if (case.case_id, method) in done:
                    continue
                started = time.perf_counter()
                result = adapters.retrieve(method, case.query)
                retrieval_ms = round(1000 * (time.perf_counter() - started), 3)
                row = {
                    "case_id": case.case_id, "method": method,
                    "selected_route": result.selected_route,
                    "expected_route": case.expected_route, "query_type": case.query_type,
                    "hits": [{"doc_id": h.doc_id, "score": h.score, "method": h.method}
                             for h in result.hits],
                    "trace": result.trace, "retrieval_ms": retrieval_ms,
                    "retrieval_metrics": retrieval_scores([h.doc_id for h in result.hits],
                                                            case.relevant, args.top_k),
                }
                if client:
                    t0 = time.perf_counter()
                    generated = client.generate(case.query, result, dataset)
                    row["generation_ms"] = round(1000 * (time.perf_counter() - t0), 3)
                    row["answer"] = generated.text
                    row["answer_metrics"] = answer_scores(generated.text, case.answer)
                    row["prompt_tokens"] = generated.prompt_tokens
                    row["completion_tokens"] = generated.completion_tokens
                stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                stream.flush()
                samples += 1
    return {"out": str(out), "new_evaluations": samples,
            "total_possible": len(selected) * len(methods), "signature": signature,
            "warnings": dataset.warnings}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", choices=["toy", "beir", "ragrouter"], default="toy")
    p.add_argument("--data-root", type=Path)
    p.add_argument("--split", default="test", help="BEIR qrels split; never use test for training")
    p.add_argument("--out", type=Path, required=True, help="A NEW run folder, outside version control")
    p.add_argument("--methods", default="bm25,hybrid_char3,autorag_auto")
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--limit-queries", type=int)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--chunk-chars", type=int, default=3000)
    p.add_argument("--overlap", type=int, default=250)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--generate", action="store_true", help="Explicit opt-in to local vLLM endpoint")
    p.add_argument("--endpoint", help="Only local HTTP loopback, e.g. http://127.0.0.1:8001/v1")
    p.add_argument("--model", help="Must match model name returned by your local vLLM server")
    p.add_argument("--max-output-tokens", type=int, default=256)
    return p.parse_args(argv)


def main() -> None:
    try:
        print(json.dumps(run(parse_args()), indent=2))
    except (FileNotFoundError, FileExistsError, ValueError, OSError) as e:
        print(f"Benchmark error: {e}", file=sys.stderr)
        raise SystemExit(2) from e


if __name__ == "__main__":
    main()

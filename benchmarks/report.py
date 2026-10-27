"""Deterministic aggregation of independent retrieval and answer metrics."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import random
import statistics
from typing import Any

RETRIEVAL_KEYS = ("ndcg_at_k", "recall_at_k", "precision_at_k", "mrr_at_k")
ANSWER_KEYS = ("exact_match", "token_f1")


def _mean(rows: list[dict], section: str, key: str) -> float | None:
    nums = [row[section].get(key) for row in rows if row.get(section) and
            isinstance(row[section].get(key), (int, float))]
    return round(statistics.mean(nums), 5) if nums else None


def _percentile(numbers: list[float], proportion: float) -> float | None:
    if not numbers:
        return None
    numbers = sorted(numbers)
    index = max(0, min(len(numbers)-1, int((len(numbers)-1)*proportion + .999999)))
    return round(numbers[index], 3)


def _bootstrap_paired(rows_a: dict[str, float], rows_b: dict[str, float],
                      *, seed: int = 42, reps: int = 500) -> dict:
    ids = sorted(set(rows_a) & set(rows_b))
    if len(ids) < 2:
        return {"n": len(ids), "mean_delta": None, "ci95": None}
    diffs = [rows_a[key] - rows_b[key] for key in ids]
    rng = random.Random(seed)
    boot = sorted(statistics.mean(rng.choice(diffs) for _ in diffs) for _ in range(reps))
    return {"n": len(ids), "mean_delta": round(statistics.mean(diffs), 5),
            "ci95": [round(boot[int(reps*.025)], 5), round(boot[min(reps-1, int(reps*.975))], 5)]}


def aggregate(run_dir: Path, *, baseline: str = "hybrid_char3", seed: int = 42) -> dict[str, Any]:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in (run_dir / "results.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["method"]].append(row)
    summaries = {}
    for method, items in sorted(grouped.items()):
        timings = [x["retrieval_ms"] for x in items]
        summary = {"evaluations": len(items), "retrieval_ms_p50": _percentile(timings, .5),
                   "retrieval_ms_p95": _percentile(timings, .95),
                   "retrieval_ms_mean": round(statistics.mean(timings), 3) if timings else None,
                   "mean_retrieved_sources": round(statistics.mean(len(x["hits"]) for x in items), 3)}
        for name in RETRIEVAL_KEYS:
            summary[name] = _mean(items, "retrieval_metrics", name)
        summary["retrieval_labeled_queries"] = sum(x["retrieval_metrics"]["ndcg_at_k"] is not None for x in items)
        summary["routing_labeled_queries"] = sum(x["expected_route"] is not None for x in items)
        valid_route = [x for x in items if x["expected_route"] is not None]
        summary["routing_accuracy_diagnostic"] = (round(sum(x["selected_route"] == x["expected_route"]
                                                       for x in valid_route)/len(valid_route), 5)
                                                   if valid_route else None)
        if manifest["generation_enabled"]:
            for name in ANSWER_KEYS:
                summary[name] = _mean(items, "answer_metrics", name)
            summary["answer_labeled_queries"] = sum(x.get("answer_metrics", {}).get("exact_match") is not None for x in items)
            for unit in ("prompt_tokens", "completion_tokens"):
                actual = [x[unit] for x in items if isinstance(x.get(unit), int)]
                summary[f"total_{unit}"] = sum(actual) if actual else None
            summary["generation_ms_p95"] = _percentile([x["generation_ms"] for x in items], .95)
        summaries[method] = summary
    deltas = {}
    if baseline in grouped:
        ref = {r["case_id"]: r["retrieval_metrics"]["ndcg_at_k"] for r in grouped[baseline]
               if r["retrieval_metrics"]["ndcg_at_k"] is not None}
        for method, items in grouped.items():
            if method == baseline:
                continue
            this = {r["case_id"]: r["retrieval_metrics"]["ndcg_at_k"] for r in items
                    if r["retrieval_metrics"]["ndcg_at_k"] is not None}
            deltas[method] = _bootstrap_paired(this, ref, seed=seed)
    summary = {"manifest": manifest, "methods": summaries, "paired_ndcg_delta_vs_" + baseline: deltas,
               "warning": "Pilot reference metrics, not SOTA: compare identical corpora, preprocessing, qrels, LLM and budget for a paper."}
    return summary


def generate_report(run_dir: Path, baseline: str = "hybrid_char3") -> tuple[Path, Path]:
    result = aggregate(run_dir, baseline=baseline)
    (run_dir / "summary.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest = result["manifest"]
    lines = ["# AutoRAG Router — Evaluation Report", "", f"- Dataset: `{manifest['dataset']}`",
             f"- Queries selected: {manifest['selected_queries']} (total {manifest['total_queries']})",
             f"- Original documents: {manifest['dataset_original_documents']}; chunks: {manifest['indexed_chunks']}",
             f"- Code revision: `{manifest['source_git_sha'] or 'not available; code digest in manifest'}`",
             f"- Reproducibility signature: `{manifest['signature']}`",
             f"- Generation enabled: {manifest['generation_enabled']}", "",
             "| Method | N | qrels N | nDCG@k | Recall@k | P95 retrieval ms |",
             "|---|---:|---:|---:|---:|---:|"]
    for name, stats in sorted(result["methods"].items()):
        def fmt(x):
            return "N/A" if x is None else str(x)
        lines.append(f"| {name} | {stats['evaluations']} | {stats['retrieval_labeled_queries']} | "
                     f"{fmt(stats['ndcg_at_k'])} | {fmt(stats['recall_at_k'])} | {fmt(stats['retrieval_ms_p95'])} |")
    lines += ["", "## Limitations", ""]
    lines += [f"- {warning}" for warning in manifest["limitations"] + manifest["warnings"]]
    lines += ["", "**No results were produced for any model/baseline not present in this manifest.**", ""]
    out = run_dir / "report.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out, run_dir / "summary.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--baseline", default="hybrid_char3")
    args = parser.parse_args()
    out, data = generate_report(args.run_dir, args.baseline)
    print(f"Generated: {out}\nGenerated: {data}")


if __name__ == "__main__":
    main()

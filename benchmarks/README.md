# AutoRAG Router — Local Scientific Benchmark Harness

**Status: runnable evaluation foundation, NOT completed scientific benchmark.**

This separate `benchmarks/` package exercises the **existing** Python AutoRAG engine and compares it with transparent lexical baselines. It does not alter `autorag/`, the public browser demo or Vercel. All datasets, model weights, private documents and results stay on the local machine. No API keys or paid services are necessary.

## Exactly what this implements

- Deterministic toy diagnostic suite (five queries, six synthetic source documents; **not publication evidence**).
- BEIR `corpus.jsonl` + `queries.jsonl` + `qrels/<split>.tsv` loader with graded source-level qrels and stable chunk-parent mapping.
- RAGRouter-Bench `Corpus.json` and `Question.json` loader. Reads `text`/`context`, original IDs, answer, supporting facts. **If supporting facts are snippets rather than document IDs, retrieval labels are unavailable and retrieval metrics are N/A.** Never confuse factual/reasoning/summary question types with optimal RAG strategies.
- True repository engine adapter (`AutoRAGEngine`) with a frozen in-memory corpus, plus `bm25` and `hybrid_char3` baselines. Optional forced modes (`autorag_graph_tagged`, `autorag_agentic_decomposition`, `autorag_structured_metadata`, `autorag_multimodal_text`) are explicitly **not equivalent** to full GraphRAG / agentic research implementations.
- Source-level `nDCG@k`, `Recall@k`, `Precision@k`, `MRR@k`; toy route-label diagnostic; p50/p95 retrieval latency; optional lexical answer EM/token F1; paired bootstrap difference in nDCG.
- Optional **loopback-only** OpenAI-compatible local vLLM endpoint; shared model and prompts for all methods; token usage when the model returns it.
- Content/code fingerprint, fixed seeded query subsampling, no qrels used for ranking, append-only JSONL with strict resume validation, JSON/Markdown report. No model downloads or GPU operations by default.

## Quick start — zero GPU or external downloads

From repository root with Python >=3.11 and regular project dependencies installed:

```bash
python -m pip install -e '.[dev]'
python -m benchmarks.spark_check
python -m benchmarks.run --dataset toy --out benchmarks/runs/toy-01
python -m benchmarks.report --run-dir benchmarks/runs/toy-01
python -m pytest -q
```

`benchmarks/runs/` is ignored by Git. Use a **new run directory** each time; interrupted runs may be resumed with identical arguments and `--resume`. Do not report these toy numbers as evidence of research superiority.

## BEIR retrieval evaluation (public benchmark)

Download one dataset from the official [BEIR repository](https://github.com/beir-cellar/beir), respecting its terms, and extract locally (e.g. `~/datasets/beir/scifact`). Files must include:

```text
scifact/
  corpus.jsonl
  queries.jsonl
  qrels/test.tsv
```

```bash
python -m benchmarks.run --dataset beir --data-root ~/datasets/beir/scifact \
  --split test --methods bm25,hybrid_char3,autorag_auto \
  --limit-queries 150 --seed 42 --top-k 5 --out benchmarks/runs/scifact-pilot
python -m benchmarks.report --run-dir benchmarks/runs/scifact-pilot
```

No answer-generation metric is computed in retrieval-only mode. Do not use `test` results to tune a learned router; reserve official train/dev splits for model selection.

## RAGRouter-Bench pilot

The reference [RAGRouter-Bench](https://github.com/ziqiwang0908/RAGRouter-Bench) supplies corpora and questions as JSON arrays. This adapter expects an extracted **individual dataset directory** containing `Corpus.json` and `Question.json` (not the entire benchmark repository root). It supports `doc_id` or `id` and question `question_id` or `id`, with `text` or `context` for document bodies.

```bash
python -m benchmarks.run --dataset ragrouter \
  --data-root ~/datasets/ragrouter/musique \
  --limit-queries 100 --seed 42 --out benchmarks/runs/musique-pilot
python -m benchmarks.report --run-dir benchmarks/runs/musique-pilot
```

**Important:** many `supporting_facts` are snippets, not original document identifiers. The harness intentionally reports retrieval scores as **N/A** for these queries. Reference answers enable optional lexical answer evaluation, but no scientific comparison against the five full published paradigms is claimed. A proper paper requires a validated passage-to-document mapping, official splits, comparable graph/vector/iterative backends and a pre-registered evaluation protocol.

## DGX Spark / Qwen3.8-Flash-Next FP4-Local

One 128-GB NVIDIA DGX Spark can be used to run the [NVIDIA FP4-local model](https://huggingface.co/nvidia/Qwen3.8-Flash-Next-FP4-Local). The model card indicates **approximately 96 GiB checkpoint footprint** and that a **specific community vLLM build and model-specific flags** are required until upstream support is available. Follow NVIDIA's up-to-date [DGX Spark recipe](https://build.nvidia.com/spark/vllm/intermediate); do **not** assume ordinary upstream `vllm serve` works. This repository intentionally does not download the ~100-GB weights, launch a container, expose a network port or alter Spark settings.

After **you** verify a compatible vLLM server on `127.0.0.1:8001` and confirm the model name returned by `/v1/models`:

```bash
python -m benchmarks.run --dataset toy --out benchmarks/runs/toy-qwen-01 \
  --generate --endpoint http://127.0.0.1:8001/v1 \
  --model nvidia/Qwen3.8-Flash-Next-FP4-Local --max-output-tokens 256
python -m benchmarks.report --run-dir benchmarks/runs/toy-qwen-01
```

**Model endpoint is restricted to loopback.** For remote access to Spark from a laptop, use an SSH tunnel to a local loopback port (do not expose vLLM publicly). The `--model` must exactly match the server's configured model identifier. All systems get the same prompt, evidence character cap and decoding settings. Recorded model answers remain **local run artifacts**, never committed.

## Experimental validity and performance limitations

1. No trained routing policy, oracle or neural retriever is implemented here. `hybrid_char3` means BM25 + **character-trigram**, not dense embeddings. Any performance numbers are for these implementations alone.
2. AutoRAG currently uses a full corpus scan for lexical retrieval. Full `7,727 × multiple-method` evaluation against 21K+ sources needs optimized indexing, true adapters and careful timing controls before an academic claim. Start with a pilot; store original and chunk counts in every manifest.
3. The runner measures retrieval wall time only. Generated answers measure generation time and tokens separately; **there is no cost estimate** until hardware power and wall-time measurements are collected. CPU/GPU throughput comparisons require independent profiling; no unsupported financial savings claim.
4. `exact_match` and `token_f1` are reference-string checks, **not an LLM judge, semantic accuracy or hallucination/faithfulness check**. If a question has no reference answer, these are null rather than zero.
5. In RAGRouter-Bench, query types (`factual`, `reasoning`, `summary`) are **not** oracle route labels. Only explicitly supplied diagnostic labels are scored for route-label accuracy.
6. Single fixed chunking and evidence budgets are used across methods. Changing corpus, chunking, top-k, policy, source code or model invalidates resume fingerprints; start a new run for a changed experiment.
7. Toy relevance labels are synthetic. BEIR qrels need official split and complete corpus; never filter candidate documents by qrels or answers. Baseline ranking never sees labels.
8. This proof-of-concept does not implement benchmark-wide caching, distributed indexing, native graph building, a semantic reranker, retriever parity with the RAGRouter-Bench paper, trained comparator policies, formal significance adjustments, or a calibrated faithfulness grader. Those are **remaining research tasks**.

## Files

- `datasets.py`: source loaders, deterministic chunking, source provenance.
- `methods.py`: actual engine, BM25, character-hybrid adapters.
- `metrics.py`: explicit rank and lexical answer metrics.
- `run.py`: deterministic experiment runner and strict resume checks.
- `generation.py`: opt-in local-only Qwen/vLLM chat completions.
- `report.py`: reproducible JSON/Markdown summaries and paired confidence intervals.
- `spark_check.py`: read-only DGX/CPU/GPU environment check.
- `configs/spark-qwen38-fp4.json`: model card and verified usage references, no secrets.

## Next work after pilot

Validate real Spark inference and record actual throughput; add an indexed retrieval path for full corpora, a true dense baseline and parity-checked graph/iterative methods; derive gold relevance from source annotations without answer leakage; freeze train/dev/test splits; evaluate a proposed novel routing algorithm on held-out test queries with multiple seeds. Record exact git SHA, hardware and benchmark version, and independent significance testing in any future research report.

**Owner rule:** no unattended GitHub updates or Vercel deploys. Future publishing requires explicit user approval for that specific task; this initial benchmark addition was explicitly requested.

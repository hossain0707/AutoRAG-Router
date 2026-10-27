"""Offline benchmark regression tests. No network, paid APIs or GPU required."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from benchmarks.datasets import load_beir, load_ragrouter, toy_dataset
from benchmarks.generation import LocalChatClient
from benchmarks.methods import BenchMethods
from benchmarks.metrics import answer_scores, retrieval_scores
from benchmarks.report import aggregate, generate_report
from benchmarks.run import parse_args, run


def test_toy_dataset_valid_and_parent_provenance():
    data = toy_dataset()
    assert len(data.cases) == 5
    assert len(set(data.parents.values())) == 6
    assert all(len(d.text) <= 3000 for d in data.documents)


def test_gold_metrics_at_k_and_no_gold():
    result = retrieval_scores(["a", "c"], {"a": 2.0, "b": 1.0}, 2)
    assert result["recall_at_k"] == pytest.approx(0.5)
    assert result["precision_at_k"] == pytest.approx(0.5)
    assert 0 < result["ndcg_at_k"] <= 1.0
    assert result["mrr_at_k"] == pytest.approx(1.0)
    assert retrieval_scores(["a"], None, 2)["ndcg_at_k"] is None
    assert retrieval_scores([], {}, 2)["recall_at_k"] is None
    assert answer_scores("The 20 DAYS", "the 20 days")["exact_match"] == 1.0
    assert answer_scores("a", "a b")["token_f1"] == pytest.approx(2 / 3)


def test_core_engine_is_actually_invoked_and_norag():
    data = toy_dataset()
    methods = BenchMethods(data.documents, data.parents, 5)
    out = methods.retrieve("autorag_auto", "What was the Q2 2026 revenue total?")
    assert out.selected_route == "structured"
    assert "revenue" in [h.doc_id for h in out.hits]
    assert out.trace[0] == "policy:structured"
    no = methods.retrieve("autorag_auto", "Hello")
    assert no.selected_route == "no_rag" and not no.hits
    hybrid = methods.retrieve("hybrid_char3", "annual paid leave")
    assert hybrid.hits[0].doc_id == "leave"
    with pytest.raises(ValueError):
        methods.retrieve("unknown", "annual paid leave")


def test_beir_loader_preserves_full_candidate_set(tmp_path):
    root = tmp_path / "scifact"
    (root / "qrels").mkdir(parents=True)
    (root / "corpus.jsonl").write_text('\n'.join([
        json.dumps({"_id": "doc1", "title": "Carbon", "text": "Carbon is an element."}),
        json.dumps({"_id": "doc2", "text": "Unrelated foobar distractor."})
    ]) + '\n')
    (root / "queries.jsonl").write_text(json.dumps({"_id": "q1", "text": "What is carbon?"}) + '\n')
    (root / "qrels" / "test.tsv").write_text("query-id\tcorpus-id\tscore\nq1\tdoc1\t2\n")
    data = load_beir(root)
    assert len(data.documents) == 2
    assert set(data.parents.values()) == {"doc1", "doc2"}
    assert data.cases[0].relevant == {"doc1": 2.0}


def test_ragrouter_loader_does_not_invent_qrels_from_snippets(tmp_path):
    root = tmp_path / "musique"
    root.mkdir()
    (root / "Corpus.json").write_text(json.dumps([
        {"id": 0, "title": "A", "context": "A" * 5000},
        {"id": 1, "title": "B", "context": "B" * 4000},
    ]))
    (root / "Question.json").write_text(json.dumps([
        {"id": "q1", "question": "Where was A?", "answer": "Earth",
         "type": "factual", "supporting_facts": ["A was found on Earth"]},
        {"id": "q2", "question": "Where was B?", "supporting_facts": [0, 1]}
    ]))
    data = load_ragrouter(root)
    assert len(data.documents) > 2
    assert data.cases[0].relevant is None
    assert data.cases[0].query_type == "factual"
    assert data.cases[0].expected_route is None
    assert data.cases[1].relevant == {"0": 1, "1": 1}
    assert data.warnings


def test_run_resume_and_report(tmp_path):
    dest = tmp_path / "run"
    argv = ["--dataset", "toy", "--out", str(dest), "--limit-queries", "3", "--seed", "3"]
    first = run(parse_args(argv))
    assert first["new_evaluations"] == 9
    saved = (dest / "results.jsonl").read_text()
    second = run(parse_args(argv + ["--resume"]))
    assert second["new_evaluations"] == 0
    assert (dest / "results.jsonl").read_text() == saved
    with pytest.raises(ValueError, match="Cannot resume"):
        run(parse_args(argv + ["--resume", "--seed", "9"]))
    with pytest.raises(FileExistsError):
        run(parse_args(argv))
    stats = aggregate(dest)
    assert "bm25" in stats["methods"] and "autorag_auto" in stats["methods"]
    report, json_file = generate_report(dest)
    assert report.exists() and json_file.exists()
    assert "Evaluation Report" in report.read_text()


def test_no_external_api_and_unsafe_endpoints_rejected(tmp_path):
    for endpoint in ("https://api.openai.com/v1", "http://api.openai.com/v1",
                     "http://example.com/v1", "file:///tmp/model", "http://127.0.0.1:80/v1?key=secret"):
        with pytest.raises(ValueError):
            LocalChatClient(endpoint, "any")
    assert LocalChatClient("http://127.0.0.1:8001/v1", "qwen").model == "qwen"
    args = parse_args(["--out", str(tmp_path / "external"), "--generate",
                       "--endpoint", "https://api.openai.com/v1", "--model", "paid"])
    with pytest.raises(ValueError):
        run(args)
    assert not (tmp_path / "external").exists()


def test_optional_local_generation_path_using_stub(tmp_path, monkeypatch):
    from benchmarks.generation import Generation
    monkeypatch.setattr(LocalChatClient, "generate",
                        lambda self, query, retrieval, dataset: Generation("720000 USD", 12, 3))
    dest = tmp_path / "stubbed-qwen"
    args = parse_args(["--dataset", "toy", "--out", str(dest), "--limit-queries", "1",
                       "--methods", "autorag_auto", "--generate",
                       "--endpoint", "http://127.0.0.1:8001/v1", "--model", "test-local"])
    output = run(args)
    assert output["new_evaluations"] == 1
    row = json.loads((dest / "results.jsonl").read_text())
    assert row["answer"] == "720000 USD"
    assert row["prompt_tokens"] == 12 and row["completion_tokens"] == 3
    assert "answer_metrics" in row
    assert aggregate(dest)["methods"]["autorag_auto"]["total_completion_tokens"] == 3

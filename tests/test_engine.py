from autorag.models import Document, QueryRequest
from autorag.engine import AutoRAGEngine
from autorag.store import SQLiteStore


def make_engine(tmp_path):
    store = SQLiteStore(str(tmp_path / "test.sqlite"))
    store.upsert([
        Document(id="1", title="Atlas", text="Atlas sends events to Beacon for indexing.",
                 tenant_id="tenant_a", entities=["Atlas", "Beacon"]),
        Document(id="2", title="Leave policy", text="Annual paid leave is twenty days.", tenant_id="tenant_a"),
        Document(id="3", title="Restricted", text="The secret project is Cobalt.", tenant_id="tenant_b"),
    ])
    return AutoRAGEngine(store)


def test_hybrid_evidence(tmp_path):
    response = make_engine(tmp_path).query(QueryRequest(query="annual paid leave", tenant_id="tenant_a"))
    assert response.grounded and response.hits[0].document_id == "2"
    assert "twenty days" in response.answer


def test_graph(tmp_path):
    response = make_engine(tmp_path).query(QueryRequest(query="How is Atlas connected to Beacon?", tenant_id="tenant_a"))
    assert response.decision.primary == "graph"
    assert response.hits[0].document_id == "1"


def test_tenant_isolation(tmp_path):
    response = make_engine(tmp_path).query(QueryRequest(query="Cobalt secret project", tenant_id="tenant_a"))
    assert all(h.document_id != "3" for h in response.hits)
    assert "Cobalt" not in response.answer


def test_no_hallucination_when_empty(tmp_path):
    response = make_engine(tmp_path).query(QueryRequest(query="What is the policy?", tenant_id="missing"))
    assert not response.grounded
    assert response.hits == []


def test_persistence(tmp_path):
    path = str(tmp_path / "persist.db")
    SQLiteStore(path).upsert([Document(id="d", text="Persistent storage works")])
    assert SQLiteStore(path).count("default") == 1


def test_filter(tmp_path):
    response = make_engine(tmp_path).query(QueryRequest(query="annual paid leave", tenant_id="tenant_a", filters={"nonexistent":"x"}))
    assert not response.hits

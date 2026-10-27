import pytest
from autorag.models import QueryRequest
from autorag.router import route


@pytest.mark.parametrize("query,expected", [
    ("hello", "no_rag"),
    ("What is the annual leave policy?", "hybrid"),
    ("How are Atlas and Beacon connected?", "graph"),
    ("Compare the system components and analyze all dependencies", "graph"),
    ("Compare performance and security of these applications", "agentic"),
    ("Explain the architecture diagram", "multimodal"),
    ("What is the total revenue this month?", "structured"),
])
def test_auto_route(query, expected):
    assert route(QueryRequest(query=query)).primary == expected


def test_override():
    r = route(QueryRequest(query="Explain the diagram", mode="hybrid"))
    assert r.primary == "hybrid"
    assert r.confidence == 1.0

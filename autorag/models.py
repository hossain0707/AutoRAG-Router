"""Public request/response schemas. Strict limits reduce accidental resource abuse."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class Document(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=128, pattern=r"^[\w.:-]+$")
    text: str = Field(min_length=1, max_length=100_000)
    title: str = Field(default="Untitled", max_length=256)
    tenant_id: str = Field(default="default", min_length=1, max_length=64, pattern=r"^[\w-]+$")
    source: str = Field(default="local", max_length=512)
    kind: Literal["text", "pdf_text", "image_caption", "table", "code"] = "text"
    entities: list[str] = Field(default_factory=list, max_length=50)
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)


class IngestRequest(BaseModel):
    documents: list[Document] = Field(min_length=1, max_length=100)


class QueryRequest(BaseModel):
    query: str = Field(min_length=2, max_length=3000)
    tenant_id: str = Field(default="default", min_length=1, max_length=64, pattern=r"^[\w-]+$")
    mode: Literal["auto", "no_rag", "hybrid", "graph", "agentic", "multimodal", "structured"] = "auto"
    top_k: int = Field(default=5, ge=1, le=20)
    verify: bool = True
    filters: dict[str, str | int | float | bool] = Field(default_factory=dict)


class Hit(BaseModel):
    document_id: str
    title: str
    source: str
    snippet: str
    score: float
    method: str


class RoutingDecision(BaseModel):
    primary: str
    stages: list[str]
    confidence: float
    reasons: list[str]
    estimated_cost: str = "local"


class QueryResponse(BaseModel):
    answer: str
    grounded: bool
    decision: RoutingDecision
    hits: list[Hit]
    trace: list[str]
    latency_ms: float
    request_id: str


class IngestResponse(BaseModel):
    stored: int
    ids: list[str]

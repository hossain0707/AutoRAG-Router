"""FastAPI entrypoint. Set AUTORAG_API_KEY in nonlocal deployments."""
from __future__ import annotations

import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from .engine import AutoRAGEngine
from .models import IngestRequest, IngestResponse, QueryRequest, QueryResponse
from .store import SQLiteStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.engine = AutoRAGEngine(SQLiteStore(os.getenv("AUTORAG_DB", "./data/autorag.db")))
    yield


app = FastAPI(title="AutoRAG Router", version="0.1.0", lifespan=lifespan,
              description="Explainable task-adaptive retrieval, local-first demo implementation")


def authenticate(x_api_key: str | None = Header(default=None)) -> None:
    configured = os.getenv("AUTORAG_API_KEY")
    if configured and (x_api_key is None or not secrets.compare_digest(x_api_key, configured)):
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.get("/readyz")
def ready(_: None = Depends(authenticate)):
    return {"status": "ready"}


@app.get("/v1/strategies", dependencies=[Depends(authenticate)])
def strategies():
    return {"strategies": ["no_rag", "hybrid", "graph", "agentic", "multimodal", "structured"],
            "stages": ["hybrid_fallback", "evidence_check"],
            "limitations": ["offline char-3 features (not neural embeddings)",
                            "multimodal uses pre-extracted text", "responses are extractive"]}


@app.post("/v1/documents", response_model=IngestResponse, dependencies=[Depends(authenticate)])
def ingest(payload: IngestRequest):
    app.state.engine.store.upsert(payload.documents)
    return IngestResponse(stored=len(payload.documents), ids=[d.id for d in payload.documents])


@app.post("/v1/query", response_model=QueryResponse, dependencies=[Depends(authenticate)])
def query(payload: QueryRequest):
    return app.state.engine.query(payload)


@app.get("/v1/metrics", dependencies=[Depends(authenticate)])
def metrics(tenant_id: str = "default"):
    if len(tenant_id) > 64 or not all(x.isalnum() or x in "_-" for x in tenant_id):
        raise HTTPException(status_code=422, detail="Invalid tenant_id")
    return {"tenant_id": tenant_id, "indexed_documents": app.state.engine.store.count(tenant_id)}


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(Path(__file__).parent / "static" / "index.html")

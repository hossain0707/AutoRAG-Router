"""CLI to start the API or run a local query."""
import argparse
import json
import os
from .engine import AutoRAGEngine
from .models import QueryRequest
from .store import SQLiteStore


def main():
    p = argparse.ArgumentParser(description="AutoRAG Router CLI")
    sub = p.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve", help="Start REST API and demo dashboard")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    query = sub.add_parser("query", help="Run a query against local indexed documents")
    query.add_argument("text")
    query.add_argument("--tenant", default="default")
    args = p.parse_args()
    if args.command == "serve":
        import uvicorn
        uvicorn.run("autorag.api:app", host=args.host, port=args.port)
    else:
        engine = AutoRAGEngine(SQLiteStore(os.getenv("AUTORAG_DB", "./data/autorag.db")))
        print(json.dumps(engine.query(QueryRequest(query=args.text, tenant_id=args.tenant)).model_dump(), indent=2))


if __name__ == "__main__":
    main()

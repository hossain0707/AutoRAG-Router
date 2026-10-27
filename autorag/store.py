"""Durable tenant-partitioned SQLite document store, no unsafe dynamic SQL."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from .models import Document


class SQLiteStore:
    def __init__(self, path: str = "./data/autorag.db") -> None:
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS documents (
                tenant_id TEXT NOT NULL, id TEXT NOT NULL, payload TEXT NOT NULL,
                PRIMARY KEY (tenant_id, id))""")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=15)

    def upsert(self, documents: list[Document]) -> None:
        with self._connect() as db:
            db.executemany(
                "INSERT INTO documents(tenant_id,id,payload) VALUES(?,?,?) "
                "ON CONFLICT(tenant_id,id) DO UPDATE SET payload=excluded.payload",
                [(d.tenant_id, d.id, d.model_dump_json()) for d in documents],
            )

    def list(self, tenant_id: str, max_docs: int = 2000) -> list[Document]:
        with self._connect() as db:
            rows = db.execute("SELECT payload FROM documents WHERE tenant_id=? ORDER BY id LIMIT ?",
                              (tenant_id, max_docs)).fetchall()
        return [Document.model_validate(json.loads(row[0])) for row in rows]

    def count(self, tenant_id: str) -> int:
        with self._connect() as db:
            return int(db.execute("SELECT count(*) FROM documents WHERE tenant_id=?", (tenant_id,)).fetchone()[0])

"""SQLite FTS5 memory store implementing BaseMemory (doc/intelecto.md Task 3.1).

Plan specifies aiosqlite; to stay stdlib-only this uses the built-in `sqlite3`
(FTS5 ships with CPython's bundled SQLite). The interface and schema/triggers are
identical to the plan. async methods wrap synchronous calls — fine for a
single-user assistant.
"""
import os
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass

SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'fact',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    content,
    category,
    content='memories',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
    INSERT INTO memories_fts(rowid, content, category) VALUES (new.id, new.content, new.category);
END;

CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, content, category) VALUES ('delete', old.id, old.content, old.category);
END;

CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, content, category) VALUES ('delete', old.id, old.content, old.category);
    INSERT INTO memories_fts(rowid, content, category) VALUES (new.id, new.content, new.category);
END;
"""


@dataclass
class MemoryEntry:
    id: int
    content: str
    category: str
    created_at: str
    relevance: float


class BaseMemory(ABC):
    @abstractmethod
    async def save(self, content: str, category: str = "fact") -> int: ...
    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> list[MemoryEntry]: ...
    @abstractmethod
    async def forget(self, memory_id: int) -> bool: ...
    @abstractmethod
    async def recent(self, limit: int = 20) -> list[MemoryEntry]: ...


def _fts_query(query: str) -> str:
    """Turn a free-text query into a safe FTS5 MATCH expression (OR of terms)."""
    terms = [t for t in "".join(c if c.isalnum() else " " for c in query).split() if t]
    if not terms:
        return '""'
    return " OR ".join(terms)


class MemoryStore(BaseMemory):
    def __init__(self, db_path: str):
        self.db_path = os.path.expanduser(db_path)
        self._conn = None

    async def initialize(self) -> None:
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def _c(self):
        if self._conn is None:
            raise RuntimeError("MemoryStore not initialized() yet")
        return self._conn

    async def save(self, content: str, category: str = "fact") -> int:
        cur = self._c().execute(
            "INSERT INTO memories (content, category) VALUES (?, ?)",
            (content, category),
        )
        self._c().commit()
        return int(cur.lastrowid)

    async def search(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        rows = self._c().execute(
            """
            SELECT m.id, m.content, m.category, m.created_at,
                   bm25(memories_fts) AS rank
            FROM memories_fts
            JOIN memories m ON m.id = memories_fts.rowid
            WHERE memories_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (_fts_query(query), limit),
        ).fetchall()
        out = []
        for r in rows:
            # bm25 returns negative-ish; lower = better. Map to 0..1 relevance.
            rank = r["rank"]
            relevance = 1.0 / (1.0 + abs(rank))
            out.append(MemoryEntry(r["id"], r["content"], r["category"], r["created_at"], relevance))
        return out

    async def forget(self, memory_id: int) -> bool:
        cur = self._c().execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        self._c().commit()
        return cur.rowcount > 0

    async def recent(self, limit: int = 20) -> list[MemoryEntry]:
        rows = self._c().execute(
            "SELECT id, content, category, created_at FROM memories ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [MemoryEntry(r["id"], r["content"], r["category"], r["created_at"], 1.0) for r in rows]

    async def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

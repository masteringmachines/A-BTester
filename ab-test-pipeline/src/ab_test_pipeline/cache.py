"""SQLite cache layer (FR5/FR8): one row per (variant, input) call.

Cache key = SHA256(variant_name + input_text), so identical inputs to the
same variant are never re-run (NFR1). A miss only happens for genuinely new
(variant, input) pairs, which is what lets incremental runs add examples
without re-spending tokens on the old ones.
"""
import hashlib
import sqlite3
import time
from contextlib import closing
from typing import Optional

_SCHEMA = """
CREATE TABLE IF NOT EXISTS llm_cache (
    variant     TEXT NOT NULL,
    input_hash  TEXT NOT NULL,
    output      TEXT NOT NULL,
    latency     REAL NOT NULL,
    created_at  REAL NOT NULL,
    PRIMARY KEY (variant, input_hash)
);
"""


def input_hash(variant_name: str, input_text: str) -> str:
    """SHA256 of variant_name + input_text, per the PRD's cache-key spec."""
    return hashlib.sha256(f"{variant_name}:{input_text}".encode("utf-8")).hexdigest()


class Cache:
    """Thin wrapper around a single SQLite file. One connection, reused."""

    def __init__(self, db_path: str = "ab_cache.db"):
        self.conn = sqlite3.connect(db_path)
        with closing(self.conn.cursor()) as cur:
            cur.execute(_SCHEMA)
        self.conn.commit()

    def get(self, variant: str, text: str) -> Optional[str]:
        """Return the cached output, or None on a cache miss (FR8)."""
        key = input_hash(variant, text)
        with closing(self.conn.cursor()) as cur:
            cur.execute(
                "SELECT output FROM llm_cache WHERE variant = ? AND input_hash = ?",
                (variant, key),
            )
            row = cur.fetchone()
        return row[0] if row else None

    def put(self, variant: str, text: str, output: str, latency: float) -> None:
        key = input_hash(variant, text)
        with closing(self.conn.cursor()) as cur:
            cur.execute(
                "INSERT OR REPLACE INTO llm_cache "
                "(variant, input_hash, output, latency, created_at) VALUES (?, ?, ?, ?, ?)",
                (variant, key, output, latency, time.time()),
            )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

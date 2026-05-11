from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .items import WatchItem, utc_now_iso


SCHEMA = """
CREATE TABLE IF NOT EXISTS seen_items (
    source TEXT NOT NULL,
    external_id TEXT NOT NULL,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT '',
    published_at TEXT NOT NULL DEFAULT '',
    discovered_at TEXT NOT NULL,
    raw_json TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY (source, external_id)
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    message TEXT NOT NULL DEFAULT ''
);
"""


class SeenStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def insert_if_new(self, item: WatchItem) -> bool:
        cur = self.conn.execute(
            """
            INSERT OR IGNORE INTO seen_items (
                source, external_id, name, url, description, category,
                published_at, discovered_at, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.source,
                item.external_id,
                item.name,
                item.url,
                item.description,
                item.category,
                item.published_at,
                item.discovered_at,
                json.dumps(item.raw, ensure_ascii=False, sort_keys=True),
            ),
        )
        self.conn.commit()
        return cur.rowcount == 1

    def begin_run(self) -> int:
        cur = self.conn.execute(
            "INSERT INTO runs (started_at, status) VALUES (?, ?)",
            (utc_now_iso(), "running"),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def finish_run(self, run_id: int, status: str, message: str = "") -> None:
        self.conn.execute(
            "UPDATE runs SET finished_at = ?, status = ?, message = ? WHERE id = ?",
            (utc_now_iso(), status, message[:2000], run_id),
        )
        self.conn.commit()


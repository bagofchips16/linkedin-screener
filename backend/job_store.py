"""SQLite persistence used to detect jobs not seen before."""

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "jobs.db")
_lock = threading.Lock()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS jobs ("
        "id TEXT PRIMARY KEY, data TEXT NOT NULL, first_seen TEXT NOT NULL)"
    )
    return conn


def add_new_jobs(jobs: list[dict]) -> list[dict]:
    """Insert jobs not seen before and return only those."""
    now = datetime.now(timezone.utc).isoformat()
    new_jobs = []
    with _lock, _connect() as conn:
        for job in jobs:
            cur = conn.execute(
                "INSERT OR IGNORE INTO jobs (id, data, first_seen) VALUES (?, ?, ?)",
                (job["id"], json.dumps(job), now),
            )
            if cur.rowcount:
                new_jobs.append(job)
    return new_jobs


def list_jobs(limit: int = 200) -> list[dict]:
    with _lock, _connect() as conn:
        rows = conn.execute(
            "SELECT data, first_seen FROM jobs ORDER BY first_seen DESC LIMIT ?", (limit,)
        ).fetchall()
    jobs = []
    for data, first_seen in rows:
        job = json.loads(data)
        job["first_seen"] = first_seen
        jobs.append(job)
    jobs.sort(key=lambda j: (j["first_seen"], j["score"]), reverse=True)
    return jobs

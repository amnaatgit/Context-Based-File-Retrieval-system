from __future__ import annotations

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / 'app' / 'data' / 'office_files.db'
SCHEMA_PATH = BASE_DIR / 'app' / 'models' / 'schema.sql'


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    schema = SCHEMA_PATH.read_text(encoding='utf-8')
    conn = get_connection()
    conn.executescript(schema)
    conn.commit()
    conn.close()

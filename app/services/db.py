from __future__ import annotations

import os
import re
from pathlib import Path

import psycopg2
import psycopg2.extras

BASE_DIR = Path(__file__).resolve().parents[2]
SCHEMA_PATH = BASE_DIR / 'app' / 'models' / 'schema_postgres.sql'

DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')

_QMARK_RE = re.compile(r'\?')


class _CursorWrapper:
        def __init__(self, cursor):
                self._cursor = cursor

        def fetchone(self):
                return self._cursor.fetchone()

        def fetchall(self):
                return self._cursor.fetchall()


class ConnectionWrapper:
        def __init__(self, raw_conn):
                self._raw = raw_conn

        def execute(self, sql, params=()):
                cur = self._raw.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cur.execute(_QMARK_RE.sub('%s', sql), params)
                return _CursorWrapper(cur)

        def executemany(self, sql, seq_of_params):
                cur = self._raw.cursor()
                cur.executemany(_QMARK_RE.sub('%s', sql), list(seq_of_params))

        def executescript(self, script):
                cur = self._raw.cursor()
                cur.execute(script)

        def commit(self):
                self._raw.commit()

        def close(self):
                try:
                        self._raw.commit()
                finally:
                        self._raw.close()


def _raw_connect():
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        conn.autocommit = False
        return conn


def _schema_ready(raw_conn):
        cur = raw_conn.cursor()
        cur.execute("SELECT to_regclass('public.documents')")
        row = cur.fetchone()
        return bool(row and row[0])


def init_db():
        schema = SCHEMA_PATH.read_text(encoding='utf-8')
        raw_conn = _raw_connect()
        try:
                cur = raw_conn.cursor()
                cur.execute(schema)
                raw_conn.commit()
        finally:
                raw_conn.close()


def _users_seeded(raw_conn):
        cur = raw_conn.cursor()
        cur.execute('SELECT COUNT(*) FROM users')
        row = cur.fetchone()
        return bool(row and row[0])


def get_connection():
        raw_conn = _raw_connect()
        if not _schema_ready(raw_conn):
                cur = raw_conn.cursor()
                cur.execute(SCHEMA_PATH.read_text(encoding='utf-8'))
                raw_conn.commit()
        if not _users_seeded(raw_conn):
                from app.services.seed import USERS
                cur = raw_conn.cursor()
                cur.executemany(
                        'INSERT INTO users (name, role, department, team, preferred_file_type) VALUES (%s, %s, %s, %s, %s)',
                        USERS,
                )
                raw_conn.commit()
        return ConnectionWrapper(raw_conn)

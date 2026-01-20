import os
import re
from contextlib import contextmanager
from typing import Dict, List, Tuple

from dotenv import load_dotenv
from psycopg2 import pool

load_dotenv()

_pool: pool.SimpleConnectionPool | None = None


def _get_pool() -> pool.SimpleConnectionPool:
    global _pool
    if _pool:
        return _pool
    uri = os.getenv("POSTGRES_DB_URI")
    if not uri:
        raise RuntimeError("POSTGRES_DB_URI is missing")
    _pool = pool.SimpleConnectionPool(1, 5, dsn=uri)
    return _pool


@contextmanager
def get_conn():
    conn_pool = _get_pool()
    conn = conn_pool.getconn()
    try:
        yield conn
    finally:
        conn_pool.putconn(conn)


def list_tables() -> List[str]:
    query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
          AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
        return [row[0] for row in rows]


def get_schema(tables: List[str]) -> Dict[str, List[Dict[str, str]]]:
    if not tables:
        return {}
    result: Dict[str, List[Dict[str, str]]] = {}
    query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
          AND table_name = %s
        ORDER BY ordinal_position;
    """
    with get_conn() as conn, conn.cursor() as cur:
        for table in tables:
            cur.execute(query, (table,))
            cols = cur.fetchall()
            result[table] = [
                {
                    "name": name,
                    "type": data_type,
                    "nullable": is_nullable,
                    "default": default,
                }
                for name, data_type, is_nullable, default in cols
            ]
    return result


_DENY_PATTERN = re.compile(r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke)\b", re.IGNORECASE)
_LIMIT_PATTERN = re.compile(r"\blimit\s+(\d+)", re.IGNORECASE)


def _sanitize_sql(sql: str, row_limit: int) -> str:
    cleaned = sql.strip().rstrip(";")
    if _DENY_PATTERN.search(cleaned):
        raise ValueError("Only read-only SELECT statements are allowed")
    if not cleaned.lower().startswith("select"):
        raise ValueError("Only SELECT statements are allowed")
    limit_match = _LIMIT_PATTERN.search(cleaned)
    if limit_match:
        try:
            current = int(limit_match.group(1))
            if current > row_limit:
                cleaned = _LIMIT_PATTERN.sub(f"LIMIT {row_limit}", cleaned)
        except ValueError:
            cleaned = _LIMIT_PATTERN.sub(f"LIMIT {row_limit}", cleaned)
    else:
        cleaned = f"{cleaned} LIMIT {row_limit}"
    return cleaned


def run_sql(query: str, row_limit: int = 50) -> Dict[str, List[Tuple]]:
    sanitized = _sanitize_sql(query, row_limit)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sanitized)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
    return {"columns": columns, "rows": rows}

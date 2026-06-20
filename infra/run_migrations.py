"""
Migration runner supporting Postgres and SQLite.

- If DATABASE_URL uses the sqlite scheme (sqlite:///path or sqlite:///:memory:)
  the runner looks for infra/sqlite_migrations/*.sql and applies them with
  sqlite3.executemany (executescript).
- Otherwise it falls back to the original Postgres behavior using psycopg2.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys
from urllib.parse import urlparse

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
SQLITE_MIGRATIONS_DIR = Path(__file__).parent / "sqlite_migrations"


def run_migrations(database_url: str) -> int:
    """Return 0 on success, non-zero on error."""
    parsed = urlparse(database_url)
    scheme = (parsed.scheme or "").lower()

    # SQLite branch
    if scheme.startswith("sqlite"):
        # Determine DB path
        if database_url == "sqlite:///:memory:" or parsed.path == ":memory:":
            db_path = ":memory:"
        else:
            db_path = parsed.path
            if db_path.startswith("/") and ":" in db_path:
                db_path = db_path.lstrip("/")
            if db_path == "":
                db_path = ":memory:"

        if not SQLITE_MIGRATIONS_DIR.exists():
            print("No sqlite migrations directory found; nothing to do.")
            return 0

        sql_files = sorted(SQLITE_MIGRATIONS_DIR.glob("*.sql"))
        if not sql_files:
            print("No SQLite SQL migration files found; nothing to do.")
            return 0

        try:
            import sqlite3

            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            for path in sql_files:
                print(f"Applying sqlite migration: {path.name}")
                sql = path.read_text(encoding="utf-8")
                cur.executescript(sql)
            conn.commit()
            cur.close()
            conn.close()
            print("SQLite migrations applied successfully.")
            return 0
        except Exception as exc:
            print("Error applying sqlite migrations:", exc)
            return 3

    # Postgres branch (original behavior)
    if not MIGRATIONS_DIR.exists():
        print("No migrations directory found; nothing to do.")
        return 0

    try:
        import psycopg2  # type: ignore
    except Exception:
        print("psycopg2 not installed. Install with: pip install psycopg2-binary")
        return 2

    dbname = parsed.path.lstrip("/")
    user = parsed.username
    password = parsed.password
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432

    conn = None
    try:
        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        conn.autocommit = True
        cur = conn.cursor()

        sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        if not sql_files:
            print("No SQL migration files found; nothing to do.")
            return 0

        for path in sql_files:
            print(f"Applying migration: {path.name}")
            sql = path.read_text(encoding="utf-8")
            cur.execute(sql)

        cur.close()
        print("Migrations applied successfully.")
        return 0
    except Exception as exc:
        print("Error applying migrations:", exc)
        return 3
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL") or (sys.argv[1] if len(sys.argv) > 1 else None)
    if not db_url:
        print("Usage: run_migrations.py <DATABASE_URL>\nOr set DATABASE_URL environment variable.")
        sys.exit(1)
    sys.exit(run_migrations(db_url))

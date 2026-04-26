#!/usr/bin/env python3
"""
Runtime DB isolation check (same invariants as the SQLAlchemy connect listener).

- Exits 0 immediately if SUPABASE_DB_SCHEMA is unset (local Docker / CI).
- Otherwise opens a connection via app.database and validates current_user
  (when SUPABASE_DB_ROLE is set) and leading search_path.

Run from repo root or backend dir, e.g.:

  PYTHONPATH=backend python backend/scripts/verify_isolation.py
  cd backend && PYTHONPATH=. python scripts/verify_isolation.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def main() -> int:
    from sqlalchemy import text

    from app.config import settings

    schema = (settings.supabase_db_schema or "").strip()
    if not schema:
        print("[verify_isolation] Skip: SUPABASE_DB_SCHEMA not set")
        return 0

    # Import engine after settings resolved (applies URL normalization + listeners).
    from app.database import engine

    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT current_user, current_schemas(true)")
            ).fetchone()
            if not row:
                print("[verify_isolation] FAIL: empty result from current_user/current_schemas")
                return 1
            user, schemas = row[0], row[1]
            if isinstance(schemas, (list, tuple)):
                path_list = [str(s) for s in schemas]
            elif schemas is None:
                path_list = []
            else:
                path_list = [s for s in str(schemas).strip("{}").split(",") if s]

            role = (settings.supabase_db_role or "").strip()
            if role and user != role:
                print(
                    f"[verify_isolation] FAIL: current_user={user!r} expected {role!r} "
                    "(set SUPABASE_DB_ROLE or clear it to skip role check)"
                )
                return 1
            if not path_list or path_list[0] != schema:
                print(
                    f"[verify_isolation] FAIL: search_path head {path_list!r} "
                    f"expected {schema!r} first"
                )
                return 1
            conn.execute(text("SELECT 1"))
        print("[verify_isolation] OK", {"user": user, "search_path": path_list})
        return 0
    except Exception as e:
        print(f"[verify_isolation] FAIL: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

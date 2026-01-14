"""Manual schema management only.

Phase 1 removes Alembic migrations entirely. Developers should recreate the
Postgres schema directly from `src/infra/db/models.py` using metadata create_all
or manual SQL. This file remains solely to block accidental Alembic usage.
"""

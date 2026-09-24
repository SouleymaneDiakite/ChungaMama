"""
Quick local-dev bootstrap: creates all tables directly from the SQLAlchemy
models. Fine for getting started; once the schema stabilizes, switch to
Alembic migrations instead of running this against a real environment.

Usage:
    python create_tables.py
"""
from app.db.session import engine, Base
from app.models import user, patient, escalation  # noqa: F401 — import so they register on Base

Base.metadata.create_all(bind=engine)
print("Tables created.")

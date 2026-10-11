import os
import tempfile

# Tests run against DATABASE_URL (PostgreSQL in CI). Without it, fall back to a local SQLite file.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("UPLOAD_DIR", tempfile.mkdtemp(prefix="receipt-uploads-"))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import event  # noqa: E402

import app.models  # noqa: E402, F401
from app.db.session import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

if engine.dialect.name == "sqlite":
    @event.listens_for(engine, "connect")
    def _enable_sqlite_fks(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

# No-op when Alembic has already created the schema (CI); creates it for SQLite runs.
Base.metadata.create_all(engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


SAMPLE_TEXT = """DemoMart
2025-08-20
Drip Coffee 12oz 3.50
Bagel x2 5.00
Turkey Sandwich 8.00
TOTAL 21.50
"""


@pytest.fixture
def fake_ocr(monkeypatch):
    """Replace Tesseract with a stub returning the given text (default: the sample receipt)."""
    state = {"text": SAMPLE_TEXT}
    monkeypatch.setattr("app.api.receipts.ocr_image_to_text", lambda path: state["text"])
    return state


def png_bytes() -> bytes:
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (10, 10), "white").save(buf, format="PNG")
    return buf.getvalue()

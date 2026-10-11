"""End-to-end OCR on the bundled sample image. Needs the tesseract binary (installed in CI and the Docker image)."""
import shutil
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.services.ocr import ocr_image_to_text
from app.services.parser import parse_receipt_text

SAMPLE = Path(__file__).resolve().parent.parent / "docs" / "samples" / "receipt1.png"


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="tesseract not installed")
def test_sample_receipt_end_to_end():
    r = parse_receipt_text(ocr_image_to_text(str(SAMPLE)))
    assert r["vendor_name"] == "DemoMart"
    assert r["date"] == date(2025, 8, 20)
    assert r["total"] == Decimal("21.50")
    assert sum(i["line_total"] for i in r["items"]) == Decimal("21.50")
    assert [i["category"] for i in r["items"]] == ["coffee", "bakery", "deli"]

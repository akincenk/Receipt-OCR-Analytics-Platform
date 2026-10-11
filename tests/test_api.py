import os

import pytest

from app.core.settings import settings
from app.services.ocr import OCRUnavailable
from tests.conftest import png_bytes


def upload(client, data=None, name="r.png"):
    return client.post("/api/v1/receipts/upload", files={"file": (name, data or png_bytes(), "image/png")})


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_upload_parses_and_stores_receipt(client, fake_ocr):
    r = upload(client)
    assert r.status_code == 201
    body = r.json()
    assert body | {"id": 0} == {
        "id": 0, "vendor": "DemoMart", "date": "2025-08-20", "date_detected": True, "total": 21.5, "items": 3
    }

    rec = client.get(f"/api/v1/receipts/{body['id']}").json()
    assert rec["currency"] == "USD" and rec["total"] == 21.5
    assert [(i["name"], i["qty"], i["line_total"]) for i in rec["items"]] == [
        ("Drip Coffee 12oz", 1, 3.5), ("Bagel", 2, 10.0), ("Turkey Sandwich", 1, 8.0)
    ]
    assert "image_path" not in rec  # server paths are not exposed


def test_upload_without_date_uses_today(client, fake_ocr):
    fake_ocr["text"] = "Corner Shop\nApple 1.00"
    body = upload(client).json()
    assert body["date_detected"] is False


def test_vendor_is_reused(client, fake_ocr):
    a, b = upload(client).json(), upload(client).json()
    ra, rb = (client.get(f"/api/v1/receipts/{x['id']}").json() for x in (a, b))
    assert ra["vendor_id"] == rb["vendor_id"]


def test_rejects_non_image(client, fake_ocr):
    assert upload(client, b"%PDF-1.4 not an image", "r.pdf").status_code == 415
    assert upload(client, b"GIF89a" + b"\0" * 20, "r.gif").status_code == 415


def test_rejects_unsupported_image_format(client, fake_ocr):
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (5, 5)).save(buf, format="GIF")
    r = upload(client, buf.getvalue(), "r.gif")
    assert r.status_code == 415 and "allowed" in r.json()["detail"]


def test_rejects_oversized_upload(client, fake_ocr, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_bytes", 100)
    assert upload(client, png_bytes() + b"\0" * 200).status_code == 413


def test_ocr_unavailable_is_503_and_cleans_up(client, monkeypatch):
    def boom(path):
        raise OCRUnavailable("tesseract not installed")

    monkeypatch.setattr("app.api.receipts.ocr_image_to_text", boom)
    before = set(os.listdir(settings.upload_dir)) if os.path.isdir(settings.upload_dir) else set()
    assert upload(client).status_code == 503
    assert set(os.listdir(settings.upload_dir)) == before


def test_missing_receipt_is_404(client):
    assert client.get("/api/v1/receipts/999").status_code == 404


def test_missing_file_is_422(client):
    assert client.post("/api/v1/receipts/upload").status_code == 422


def test_no_cors_by_default(client):
    r = client.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in r.headers


@pytest.fixture
def three_receipts(client, fake_ocr):
    fake_ocr["text"] = "DemoMart\n2025-08-01\nLatte 4.00\nBagel x2 3.00\nTOTAL 10.00"
    upload(client)
    fake_ocr["text"] = "DemoMart\n2025-08-15\nCroissant 6.00"
    upload(client)
    fake_ocr["text"] = "GreenGrocer\n2025-09-01\nApple x4 0.50\nTomato 3.00"
    upload(client)


def test_analytics_summary(client, three_receipts):
    assert client.get("/api/v1/analytics/summary").json() == {
        "receipts": 3, "total_spend": 21.0, "avg_per_receipt": 7.0
    }
    r = client.get("/api/v1/analytics/summary", params={"from": "2025-08-10", "to": "2025-08-31"})
    assert r.json() == {"receipts": 1, "total_spend": 6.0, "avg_per_receipt": 6.0}


def test_analytics_summary_empty(client):
    assert client.get("/api/v1/analytics/summary").json() == {
        "receipts": 0, "total_spend": 0.0, "avg_per_receipt": 0.0
    }


def test_analytics_by_vendor(client, three_receipts):
    assert client.get("/api/v1/analytics/by-vendor").json() == [
        {"vendor": "DemoMart", "total_spend": 16.0},
        {"vendor": "GreenGrocer", "total_spend": 5.0},
    ]
    assert client.get("/api/v1/analytics/by-vendor", params={"from": "2025-09-01"}).json() == [
        {"vendor": "GreenGrocer", "total_spend": 5.0}
    ]


def test_analytics_by_category(client, three_receipts):
    assert client.get("/api/v1/analytics/by-category").json() == [
        {"category": "bakery", "total_spend": 12.0},
        {"category": "produce", "total_spend": 5.0},
        {"category": "coffee", "total_spend": 4.0},
    ]


def test_analytics_date_validation(client):
    assert client.get("/api/v1/analytics/summary", params={"from": "nope"}).status_code == 422
    r = client.get("/api/v1/analytics/by-vendor", params={"from": "2025-09-01", "to": "2025-08-01"})
    assert r.status_code == 400

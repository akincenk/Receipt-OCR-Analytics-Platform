# Receipt OCR & Analytics Platform

[![CI](https://github.com/akincenk/Receipt-OCR-Analytics-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/akincenk/Receipt-OCR-Analytics-Platform/actions/workflows/ci.yml)

A REST API that takes a photo or scan of a receipt, extracts the text with Tesseract OCR, parses vendor, date, line
items and total with rule-based heuristics, stores the result in PostgreSQL and reports spend by period, vendor and
category.

## What it does

1. **Upload** (`POST /api/v1/receipts/upload`, multipart field `file`): PNG, JPEG, TIFF or WEBP up to 5 MB by default.
   The file type is checked from the bytes, not the file name; anything else is rejected with `415`, oversized files
   with `413`.
2. **OCR**: the image is converted to grayscale, upscaled 2x if narrow, and passed to Tesseract via `pytesseract`.
3. **Parse** (`app/services/parser.py`): regular expressions and keyword lists, **no machine learning**:
   - vendor = first non-empty line
   - date = first `YYYY-MM-DD` or `MM/DD/YYYY` in the first five lines (if none, the upload date is used and the
     response says `"date_detected": false`)
   - items = lines ending in a price, `Name 3.50` or `Name x2 5.00` (unit price times quantity)
   - total = the printed `TOTAL` line if present, otherwise the sum of items; subtotal/tax/cash/change lines are ignored
   - category = keyword match on the item name (`coffee`, `bakery`, `deli`, `produce`, otherwise `other`)
4. **Analytics**: receipt count, total and average spend; spend by vendor; spend by category. All accept optional
   `from` / `to` dates.

The sample in `docs/samples/receipt1.png` parses to vendor `DemoMart`, date 2025-08-20, three items and total 21.50.
CI checks this with real Tesseract.

## Stack

FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PostgreSQL 16, Tesseract (`pytesseract`, Pillow), Docker Compose,
pytest, ruff, GitHub Actions.

```
app/
  main.py               FastAPI app, /health, optional CORS
  api/receipts.py       upload (validation, storage, OCR, persist) and GET /receipts/{id}
  api/analytics.py      summary, by-vendor, by-category
  services/ocr.py       Tesseract wrapper
  services/parser.py    rule-based receipt text parser
  models/               Vendor, Receipt, ReceiptItem
  db/                   engine/session, Alembic migrations
  seed/seed_demo.py     one demo receipt without OCR
tests/                  parser unit tests, API tests (OCR stubbed), end-to-end OCR test on the sample image
docs/                   sample receipt, Postman collection
```

```mermaid
flowchart LR
  Upload[POST /receipts/upload] --> Check[size + type check] --> OCR[Tesseract] --> Parser[regex parser] --> DB[(PostgreSQL)]
  DB --> Analytics[GET /analytics/*]
```

## Quickstart

### Docker Compose

The image includes Tesseract.

```bash
docker compose up -d --build                     # Postgres + migrations + API on :8000
curl -F "file=@docs/samples/receipt1.png" http://localhost:8000/api/v1/receipts/upload
curl http://localhost:8000/api/v1/receipts/1
curl "http://localhost:8000/api/v1/analytics/summary?from=2025-01-01&to=2025-12-31"
curl http://localhost:8000/api/v1/analytics/by-vendor
curl http://localhost:8000/api/v1/analytics/by-category
open http://localhost:8000/docs
docker compose down -v
```

### Local (Python 3.11+)

```bash
brew install tesseract            # or: sudo apt-get install tesseract-ocr
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/receipts
alembic upgrade head
uvicorn app.main:app --reload
```

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/receipts` (dev only) | app and Alembic |
| `UPLOAD_DIR` | `./uploads` (`/app/uploads` in Docker, kept in a volume) | where images are stored |
| `MAX_UPLOAD_BYTES` | `5242880` (5 MB) | upload size limit |
| `CORS_ORIGINS` | empty (CORS disabled) | comma-separated list of allowed browser origins |

See `.env.example`. Compose also reads `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` from `.env`.

## API overview

Full schemas at `/docs`; a Postman collection is in `docs/`.

| Method | Path | Notes |
|---|---|---|
| GET | `/health` | liveness |
| POST | `/api/v1/receipts/upload` | `201` with id, vendor, date, `date_detected`, total, item count; `413`, `415`, `422` (no file), `503` (Tesseract missing) |
| GET | `/api/v1/receipts/{id}` | receipt with items and raw OCR text; `404` |
| GET | `/api/v1/analytics/summary` | `receipts`, `total_spend`, `avg_per_receipt` |
| GET | `/api/v1/analytics/by-vendor` | spend per vendor, highest first |
| GET | `/api/v1/analytics/by-category` | spend per item category, highest first |

Analytics endpoints take `from` and `to` (`YYYY-MM-DD`); bad dates are `422`, `from` after `to` is `400`.

## Tests

```bash
pytest
```

- `tests/test_parser.py`: parser cases (quantities, comma decimals, TOTAL vs. item sum, summary lines, date formats,
  empty input).
- `tests/test_api.py`: upload flow with OCR stubbed, upload limits and type checks, 404/422/503 paths, CORS default,
  analytics values and date filters.
- `tests/test_ocr.py`: real Tesseract on the sample image; skipped if the `tesseract` binary is not installed.

Without `DATABASE_URL`, tests use a local SQLite file. CI installs Tesseract, runs ruff, `alembic upgrade head`,
`alembic check` (models vs. migrations) and pytest against PostgreSQL 16 on Python 3.11 and 3.12, and builds the
Docker image.

## Limitations and next steps

- The parser is a set of heuristics tuned to simple one-item-per-line receipts. Real receipts with columns, wrapped
  item names, discounts, multi-currency or non-US date formats will parse poorly. Currency is always `USD`.
- Category is a small keyword list, not a classifier.
- OCR runs synchronously inside the request; large volumes would need a job queue.
- No authentication, no per-user data separation, no delete endpoint; uploaded images stay on local disk.
- Next steps: layout-aware parsing (Tesseract word boxes), a learned item classifier, async processing, object storage.

## License

MIT, see [LICENSE](LICENSE).

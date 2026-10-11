# Receipt OCR & Analytics Platform (v1)
[![CI](https://img.shields.io/badge/CI-passing-brightgreen)](#)
[![Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20Tesseract%20%7C%20Postgres%20%7C%20SQLAlchemy-blue)](#)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](#)

Production-grade API to parse receipt images into structured data and expose analytics (spend, categories, trends).

- **Stack:** FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL + Docker Compose + Tesseract (via `pytesseract`)
- **Features:** Upload receipt image → OCR → parse → store; analytics endpoints (summary, by-vendor, by-keyword category)
- **Quality:** CI (pytest), Makefile, Postman collection, ASCII-safe docs
- **Live Docs:** `http://localhost:8000/docs` (after launch)

---

## Architecture (Mermaid)
```mermaid
flowchart LR
  Client[CLI / Postman / Frontend] --> API[FastAPI]
  API --> OCR[Tesseract OCR]
  API --> Parser[Parser & Normalizer]
  API --> DB[(PostgreSQL)]
  subgraph Infra
    API --- DB
  end
```

---

## Domain Model
```mermaid
erDiagram
  Vendor ||--o{ Receipt : has
  Receipt ||--o{ ReceiptItem : contains

  Vendor {
    int id PK
    string name
  }
  Receipt {
    int id PK
    int vendor_id FK
    date d
    string currency
    numeric total
    string raw_text
    string image_path
  }
  ReceiptItem {
    int id PK
    int receipt_id FK
    string name
    int qty
    numeric unit_price
    numeric line_total
    string category
  }
```

---

## Quickstart
```bash
# 0) Prepare env
cp backend/.env.example backend/.env

# 1) Run stack
docker compose -f infra/docker-compose.yml up -d --build

# 2) Init DB
docker compose -f infra/docker-compose.yml exec api alembic upgrade head

# 3) Seed demo data
docker compose -f infra/docker-compose.yml exec api python -m app.seed.seed_demo

# 4) Demo: Upload sample receipt image
curl -F "file=@docs/samples/receipt1.png" http://localhost:8000/api/v1/receipts/upload

# 5) Analytics
curl "http://localhost:8000/api/v1/analytics/summary"
curl "http://localhost:8000/api/v1/analytics/by-vendor"
curl "http://localhost:8000/api/v1/analytics/by-category"
```

OpenAPI: `http://localhost:8000/docs`

---

## API Overview
- `GET /health` → service status
- `POST /api/v1/receipts/upload` (multipart form-data: `file`) → OCR + parse + persist
- `GET /api/v1/receipts/{id}` → receipt with items
- `GET /api/v1/analytics/summary?from=YYYY-MM-DD&to=YYYY-MM-DD` → total spend, receipts count, avg per receipt
- `GET /api/v1/analytics/by-vendor` → spend by vendor
- `GET /api/v1/analytics/by-category` → spend by keyword category (coffee/bakery/deli/produce/other)

See `docs/postman_collection.json` for ready-to-run requests.

---

## Demo Preview
> Add these files into `docs/screenshots/` and they will appear here on GitHub.

![Docs](docs/screenshots/fastapi_docs.png)
![Upload](docs/screenshots/upload_response.png)
![Analytics](docs/screenshots/analytics_summary.png)
![Postman](docs/screenshots/postman_requests.png)

---

## Roadmap
- v1 (this): Tesseract OCR + heuristic parser + analytics endpoints
- v2: Layout-aware parsing (lines/columns), ML-based item classification, currency detection, VAT parsing
- v3: Async OCR queue (Celery + Redis), S3 uploads, dashboard

---

## License
MIT

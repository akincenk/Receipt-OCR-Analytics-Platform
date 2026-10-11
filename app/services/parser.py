"""Rule-based parser for OCR'd receipt text.

Heuristics only (regular expressions and keyword lists), no ML:
- vendor: first non-empty line
- date: first YYYY-MM-DD or MM/DD/YYYY in the first 5 lines, else None
- items: lines ending in a price ("Name 3.50") or "Name x2 5.00" (unit price x quantity)
- total: the printed TOTAL line if present, otherwise the sum of items
- category: keyword match on the item name
"""
import re
from datetime import date
from decimal import Decimal

CATEGORY_KEYWORDS = {
    "coffee": ["coffee", "latte", "espresso", "americano"],
    "bakery": ["bread", "bagel", "croissant", "muffin"],
    "deli": ["sandwich", "turkey", "ham"],
    "produce": ["apple", "banana", "tomato", "lettuce"],
}

PRICE = r"(?P<price>\d+[.,]\d{2})"
PAT_QTY = re.compile(rf"^(?P<name>.+?)\s+x(?P<qty>\d+)\s+{PRICE}$", re.IGNORECASE)
PAT_SIMPLE = re.compile(rf"^(?P<name>.+?)\s+{PRICE}$")
PAT_TOTAL = re.compile(rf"^total\b.*?{PRICE}$", re.IGNORECASE)
# Summary lines that end in a price but are not items.
NON_ITEM = re.compile(r"^(sub\s*total|total|tax|vat|change|cash|card|balance)\b", re.IGNORECASE)
PAT_DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})|(\d{2})/(\d{2})/(\d{4})")


def guess_category(name: str) -> str:
    n = name.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(kw in n for kw in kws):
            return cat
    return "other"


def _price(s: str) -> Decimal:
    return Decimal(s.replace(",", "."))


def _find_date(lines: list[str]) -> date | None:
    for line in lines[:5]:
        m = PAT_DATE.search(line)
        if m:
            try:
                if m.group(1):
                    return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                return date(int(m.group(6)), int(m.group(4)), int(m.group(5)))
            except ValueError:  # e.g. 2025-13-45
                return None
    return None


def parse_receipt_text(txt: str) -> dict:
    lines = [line.strip() for line in txt.splitlines() if line.strip()]
    items = []
    printed_total = None

    for line in lines[1:]:
        m = PAT_TOTAL.match(line)
        if m:
            printed_total = _price(m.group("price"))
            continue
        if NON_ITEM.match(line):
            continue
        m = PAT_QTY.match(line)
        if m:
            qty, unit = int(m.group("qty")), _price(m.group("price"))
        else:
            m = PAT_SIMPLE.match(line)
            if not m:
                continue
            qty, unit = 1, _price(m.group("price"))
        name = m.group("name").strip()[:255]
        items.append(
            {"name": name, "qty": qty, "unit_price": unit, "line_total": unit * qty, "category": guess_category(name)}
        )

    items_sum = sum((it["line_total"] for it in items), Decimal("0.00"))
    return {
        "vendor_name": lines[0][:255] if lines else "Unknown Vendor",
        "date": _find_date(lines),
        "currency": "USD",
        "items": items,
        "total": printed_total if printed_total is not None else items_sum,
        "raw_text": txt,
    }

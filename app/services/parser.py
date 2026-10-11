import re
from datetime import date
from decimal import Decimal

CATEGORY_KEYWORDS = {
    "coffee": ["coffee", "latte", "espresso", "americano"],
    "bakery": ["bread", "bagel", "croissant", "muffin"],
    "deli": ["sandwich", "turkey", "ham"],
    "produce": ["apple", "banana", "tomato", "lettuce"],
}

def guess_category(name: str) -> str:
    n = name.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in n:
                return cat
    return "other"

def parse_receipt_text(txt: str) -> dict:
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    vendor = lines[0][:255] if lines else "Unknown Vendor"
    # Try to find a date
    d = date.today()
    for l in lines[:5]:
        m = re.search(r"(\d{4}-\d{2}-\d{2})|(\d{2}/\d{2}/\d{4})", l)
        if m:
            s = m.group(0)
            try:
                if "-" in s:
                    y, mo, da = s.split("-"); d = date(int(y), int(mo), int(da))
                else:
                    mo, da, y = s.split("/"); d = date(int(y), int(mo), int(da))
            except Exception:
                pass
            break

    items = []
    total = Decimal("0.00")

    # Patterns like: "Latte x2 5.00" or "Muffin 3.50"
    pat_qty = re.compile(r"^(?P<name>.+?)\s+x(?P<qty>\d+)\s+(?P<price>\d+[\.,]\d{2})$")
    pat_simple = re.compile(r"^(?P<name>.+?)\s+(?P<price>\d+[\.,]\d{2})$")

    for l in lines[1:]:
        l = l.replace(",", ".")
        m = pat_qty.match(l)
        if m:
            name = m.group("name").strip()
            qty = int(m.group("qty"))
            unit = Decimal(m.group("price"))
            line_total = unit * qty
            items.append({"name": name, "qty": qty, "unit_price": unit, "line_total": line_total, "category": guess_category(name)})
            total += line_total
            continue
        m = pat_simple.match(l)
        if m:
            name = m.group("name").strip()
            unit = Decimal(m.group("price"))
            items.append({"name": name, "qty": 1, "unit_price": unit, "line_total": unit, "category": guess_category(name)})
            total += unit

    return {
        "vendor_name": vendor,
        "date": d,
        "currency": "USD",
        "items": items,
        "total": total,
        "raw_text": txt,
    }

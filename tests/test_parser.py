from datetime import date
from decimal import Decimal

from app.services.parser import guess_category, parse_receipt_text
from tests.conftest import SAMPLE_TEXT


def test_parses_sample_receipt():
    r = parse_receipt_text(SAMPLE_TEXT)
    assert r["vendor_name"] == "DemoMart"
    assert r["date"] == date(2025, 8, 20)
    assert [(i["name"], i["qty"], i["unit_price"], i["line_total"], i["category"]) for i in r["items"]] == [
        ("Drip Coffee 12oz", 1, Decimal("3.50"), Decimal("3.50"), "coffee"),
        ("Bagel", 2, Decimal("5.00"), Decimal("10.00"), "bakery"),
        ("Turkey Sandwich", 1, Decimal("8.00"), Decimal("8.00"), "deli"),
    ]
    # The TOTAL line is used as the total and is not counted as an item.
    assert r["total"] == Decimal("21.50")


def test_summary_lines_are_not_items():
    r = parse_receipt_text("Shop\nApple 1.00\nSubtotal 1.00\nTax 0.10\nTotal: 1.10\nCash 5.00\nChange 3.90")
    assert [i["name"] for i in r["items"]] == ["Apple"]
    assert r["total"] == Decimal("1.10")


def test_total_falls_back_to_item_sum():
    r = parse_receipt_text("Shop\nLatte x3 4,50\nMuffin 2.25")
    assert r["total"] == Decimal("15.75")  # comma decimal separator accepted


def test_us_date_format_and_missing_or_invalid_date():
    assert parse_receipt_text("Shop\n08/20/2025\nX 1.00")["date"] == date(2025, 8, 20)
    assert parse_receipt_text("Shop\nX 1.00")["date"] is None
    assert parse_receipt_text("Shop\n2025-13-45\nX 1.00")["date"] is None


def test_empty_text():
    r = parse_receipt_text("   \n")
    assert r["vendor_name"] == "Unknown Vendor"
    assert r["items"] == [] and r["total"] == 0


def test_lines_without_prices_are_ignored():
    r = parse_receipt_text("Shop\nThank you for shopping!\nItem 2.00")
    assert [i["name"] for i in r["items"]] == ["Item"]


def test_guess_category():
    assert guess_category("ESPRESSO double") == "coffee"
    assert guess_category("Banana bunch") == "produce"
    assert guess_category("Batteries") == "other"

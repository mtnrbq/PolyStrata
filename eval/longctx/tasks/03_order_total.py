PROMPT = r'''
Implement `order_total(goods, region, codes, today, weight_g)` in `shopkit/orders.py`. `goods` is the goods subtotal
in AUD cents, `codes` the discount codes the customer entered, `today` a `datetime.date`, and `weight_g` the parcel
weight in grams. Return what the customer pays in AUD cents: the goods after discounts, plus tax, plus shipping.
Follow the shop's existing rules for discount codes, tax, regions and shipping, and reuse the project's helpers.
'''
DEFAULT_FILE = "shopkit/orders.py"
REPLACE = {"shopkit/orders.py": '''"""Orders."""
from .codes import lookup_code, normalize_sku
from .config import MAX_LINE_QTY, NO_SHIP_REGIONS, SHIPPING_TABLE, TAX_RATES
from .money import scale, to_minor


def line_total(sku: str, unit_price: str, qty: int, currency: str) -> int:
    normalize_sku(sku)
    if not isinstance(qty, int) or not 1 <= qty <= MAX_LINE_QTY:
        raise ValueError(f"quantity must be 1 to {MAX_LINE_QTY}")
    return to_minor(unit_price, currency) * qty


def shipping_cost(weight_g: int, region: str) -> int:
    if region in NO_SHIP_REGIONS:
        raise ValueError(f"no shipping to {region}")
    if weight_g <= 0:
        raise ValueError("weight must be positive")
    for limit, price in SHIPPING_TABLE:
        if weight_g <= limit:
            return price
    raise ValueError("too heavy to ship")


def order_total(goods: int, region: str, codes: list[str], today, weight_g: int) -> int:
    raise NotImplementedError
'''}

from datetime import date

from shopkit.orders import order_total

NOW = date(2026, 11, 24)


def test_no_codes():
    assert order_total(12345, "AU", [], NOW, 1500) == 12345 + 1234 + 1295   # tax 1234.5 rounds half to even


def test_percentage_codes_add_up():
    assert order_total(10000, "NZ", ["WELCOME5", "SPRING10"], NOW, 600) == 8500 + 1275 + 1295


def test_codes_are_case_insensitive_and_staff_alone_is_fine():
    assert order_total(10000, "US-CA", ["staff20"], NOW, 2000) == 8000 + 580 + 1295


def test_free_shipping_threshold_uses_goods_before_discount():
    # 15500 before the 5% discount is over BIGSHIP's 15000; 14725 after it is not
    assert order_total(15500, "AU", ["WELCOME5", "BIGSHIP"], NOW, 9000) == 14725 + 1472


def test_free_shipping_threshold_is_inclusive():
    june = date(2026, 6, 1)
    assert order_total(5000, "AU", ["FREESHIP"], june, 3000) == 5000 + 500
    assert order_total(4999, "AU", ["FREESHIP"], june, 3000) == 4999 + 500 + 2450


def test_collected_in_store_region_pays_no_shipping():
    assert order_total(2000, "US-OR", [], NOW, 100) == 2000


def test_non_combinable_code_with_another():
    raises(ValueError, order_total, 10000, "AU", ["STAFF20", "WELCOME5"], NOW, 500)


def test_expired_codes():
    raises(ValueError, order_total, 10000, "AU", ["SPRING10"], date(2026, 12, 1), 500)
    raises(ValueError, order_total, 10000, "AU", ["FREESHIP"], NOW, 500)


def test_unknown_region():
    raises(ValueError, order_total, 10000, "UK", [], NOW, 500)

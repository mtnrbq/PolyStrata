```python
# file: shopkit/orders.py
"""Orders."""
from .codes import lookup_code, normalize_sku
from .config import MAX_LINE_QTY, NO_SHIP_REGIONS, SHIPPING_TABLE, TAX_RATES
from .money import format_money, scale, to_minor


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
    if region not in TAX_RATES:
        raise ValueError(f"unknown region {region!r}")
    found = [lookup_code(c, today) for c in codes]
    if len(found) > 1 and not all(comb for _, _, comb in found):
        raise ValueError("a code that cannot be combined was used with another")
    pct = sum(v for k, v, _ in found if k == "pct")
    after = goods - scale(goods, pct)
    tax = scale(after, TAX_RATES[region])
    free = region in NO_SHIP_REGIONS or any(k == "ship" and goods >= v for k, v, _ in found)
    return after + tax + (0 if free else shipping_cost(weight_g, region))


def receipt_line(sku: str, qty: int, line_minor: int, currency: str) -> str:
    return f"{normalize_sku(sku)} x{qty}  {format_money(line_minor, currency)}"
```

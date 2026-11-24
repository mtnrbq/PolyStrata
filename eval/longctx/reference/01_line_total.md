```python
# file: shopkit/orders.py
"""Orders."""
from .codes import normalize_sku
from .config import MAX_LINE_QTY
from .money import to_minor


def line_total(sku: str, unit_price: str, qty: int, currency: str) -> int:
    normalize_sku(sku)
    if not isinstance(qty, int) or not 1 <= qty <= MAX_LINE_QTY:
        raise ValueError(f"quantity must be 1 to {MAX_LINE_QTY}")
    return to_minor(unit_price, currency) * qty


def shipping_cost(weight_g: int, region: str) -> int:
    raise NotImplementedError


def order_total(goods: int, region: str, codes: list[str], today, weight_g: int) -> int:
    raise NotImplementedError
```

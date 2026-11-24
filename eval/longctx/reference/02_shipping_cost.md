```python
# file: shopkit/orders.py
"""Orders."""
from .config import NO_SHIP_REGIONS, SHIPPING_TABLE


def line_total(sku: str, unit_price: str, qty: int, currency: str) -> int:
    raise NotImplementedError


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
```

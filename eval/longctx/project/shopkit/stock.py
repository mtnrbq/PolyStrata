"""Stock levels and reservations. A reservation holds units for an order until it ships or is released."""
from .codes import normalize_sku
from .events import emit

_ON_HAND = {}
_RESERVED = {}


def set_stock(sku: str, qty: int):
    """Set the units on hand for a SKU. Reservations are kept."""
    sku = normalize_sku(sku)
    if qty < 0:
        raise ValueError("stock cannot be negative")
    _ON_HAND[sku] = qty
    emit("stock.set", sku=sku, qty=qty)


def available(sku: str) -> int:
    """Units on hand that are not reserved."""
    sku = normalize_sku(sku)
    return _ON_HAND.get(sku, 0) - _RESERVED.get(sku, 0)


def reserve(sku: str, qty: int) -> bool:
    """Reserve `qty` units if that many are available; True if it did, False (and nothing reserved) if not."""
    sku = normalize_sku(sku)
    if qty < 1:
        raise ValueError("reserve at least one unit")
    if qty <= available(sku):
        _RESERVED[sku] = _RESERVED.get(sku, 0) + qty
        emit("stock.reserved", sku=sku, qty=qty)
        return True
    emit("stock.short", sku=sku, qty=qty)
    return False


def release(sku: str, qty: int):
    """Give back up to `qty` reserved units."""
    sku = normalize_sku(sku)
    _RESERVED[sku] = max(0, _RESERVED.get(sku, 0) - qty)
    emit("stock.released", sku=sku, qty=qty)


def reset():
    _ON_HAND.clear()
    _RESERVED.clear()

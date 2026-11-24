"""SKUs and discount codes."""
import re
from datetime import date

from .events import emit

_SKU = re.compile(r"[A-Z]{3}[0-9]{4,6}")


def normalize_sku(raw: str) -> str:
    """' abc-1234 ' -> 'ABC1234'. Spaces and hyphens are dropped and letters upper-cased; the result must be three
    letters followed by 4 to 6 digits, or ValueError."""
    s = raw.strip().upper().replace("-", "").replace(" ", "")
    if not _SKU.fullmatch(s):
        raise ValueError(f"bad SKU {raw!r}")
    return s


# code -> (kind, value, last day it is valid, combinable with other codes)
#   kind "pct":  `value` is a fraction taken off the goods subtotal, before tax. Percentage codes add up:
#                WELCOME5 and SPRING10 together take 15% off.
#   kind "ship": shipping is free when the goods subtotal before any discount is at least `value` AUD cents.
# A code that is not combinable cannot be used together with any other code: such an order is rejected.
DISCOUNT_CODES = {
    "STAFF20": ("pct", 0.20, date(2099, 12, 31), False),
    "WELCOME5": ("pct", 0.05, date(2026, 12, 31), True),
    "SPRING10": ("pct", 0.10, date(2026, 11, 30), True),
    "FREESHIP": ("ship", 5000, date(2026, 6, 30), True),
    "BIGSHIP": ("ship", 15000, date(2027, 12, 31), True),
}


def lookup_code(code: str, today: date):
    """(kind, value, combinable) for a code, case-insensitive. ValueError if it is unknown or past its last day."""
    entry = DISCOUNT_CODES.get(code.strip().upper())
    if entry is None or today > entry[2]:
        emit("code.rejected", code=code)
        raise ValueError(f"invalid discount code {code!r}")
    kind, value, _, combinable = entry
    emit("code.accepted", code=code)
    return kind, value, combinable

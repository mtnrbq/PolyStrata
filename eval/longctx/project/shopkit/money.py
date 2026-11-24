"""Money in shopkit is always an int count of minor units: cents for AUD, NZD and USD, yen for JPY, fils for BHD.
Never use floats for money."""
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

# Minor-unit places per currency. Any other currency is rejected with ValueError.
CURRENCY_DECIMALS = {"AUD": 2, "NZD": 2, "USD": 2, "JPY": 0, "BHD": 3}


def _places(currency: str) -> int:
    if currency not in CURRENCY_DECIMALS:
        raise ValueError(f"unsupported currency {currency!r}")
    return CURRENCY_DECIMALS[currency]


def to_minor(amount: str, currency: str) -> int:
    """A decimal string to minor units, rounding half to even: '0.125' AUD -> 12, '0.135' AUD -> 14,
    '1234.5' JPY -> 1234. ValueError for a non-string or a malformed amount."""
    places = _places(currency)
    try:
        d = Decimal(amount.strip())
    except (InvalidOperation, AttributeError):
        raise ValueError(f"bad amount {amount!r}") from None
    if not d.is_finite():
        raise ValueError(f"bad amount {amount!r}")
    return int(d.scaleb(places).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


def scale(minor: int, factor) -> int:
    """minor * factor, rounded half to even to a whole minor unit. Used for tax and percentage discounts."""
    return int((Decimal(minor) * Decimal(str(factor))).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


def format_money(minor: int, currency: str) -> str:
    """123450 AUD -> 'AUD 1,234.50'; -300 AUD -> '-AUD 3.00'; 1235 JPY -> 'JPY 1,235'; 5 BHD -> 'BHD 0.005'."""
    places = _places(currency)
    sign = "-" if minor < 0 else ""
    whole, frac = divmod(abs(minor), 10 ** places)
    body = f"{whole:,}" + (f".{frac:0{places}d}" if places else "")
    return f"{sign}{currency} {body}"

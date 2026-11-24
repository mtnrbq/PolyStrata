PROMPT = r'''
A customer in NZ was charged 184 cents of tax on a 1,233-cent order. 15% of 1233 is 184.95, so the tax should have
been 185. Find the cause and fix it where it starts, so that every caller gets it right, and keep the project's
existing rounding rules.
'''
DEFAULT_FILE = "shopkit/money.py"
REPLACE = {"shopkit/orders.py": "@orders_full.py"}
PATCHES = {"shopkit/money.py": [
    ("    return int((Decimal(minor) * Decimal(str(factor))).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))",
     "    return int(Decimal(minor) * Decimal(str(factor)))")]}

from datetime import date

from shopkit.money import scale
from shopkit.orders import order_total


def test_the_reported_order():
    assert order_total(1233, "NZ", [], date(2026, 11, 24), 100) == 1233 + 185 + 895


def test_scale_rounds_instead_of_truncating():
    assert scale(1233, 0.15) == 185
    assert scale(1000, 0.0725) == 72 and scale(999, 0.5) == 500


def test_scale_rounds_half_to_even():
    assert scale(125, 0.1) == 12 and scale(135, 0.1) == 14 and scale(5, 0.5) == 2


def test_negative_amounts():
    assert scale(-1233, 0.15) == -185


def test_result_is_an_int():
    assert type(scale(1000, 0.0725)) is int

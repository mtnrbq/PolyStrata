PROMPT = r'''
Implement `line_total(sku, unit_price, qty, currency)` in `shopkit/orders.py`. It returns the total for one order
line in minor units of `currency`. Follow the project's existing rules for SKUs, line quantities, currencies and
amounts, and reuse its helpers rather than writing new ones.
'''
DEFAULT_FILE = "shopkit/orders.py"

from shopkit.orders import line_total


def test_basic():
    assert line_total("ABC1234", "19.99", 2, "AUD") == 3998


def test_sku_is_normalised_not_rejected():
    assert line_total(" abc-1234 ", "1.00", 1, "AUD") == 100
    assert line_total("xyz 123456", "1", 3, "USD") == 300


def test_rounds_half_to_even_like_the_project():
    assert line_total("ABC1234", "0.125", 1, "AUD") == 12
    assert line_total("ABC1234", "0.135", 3, "AUD") == 42
    assert line_total("ABC1234", "1234.5", 1, "JPY") == 1234


def test_three_decimal_currency():
    assert line_total("ABC1234", "1.2345", 2, "BHD") == 2468


def test_quantity_limit():
    assert line_total("ABC1234", "1", 24, "AUD") == 2400
    for qty in (25, 0, -1):
        raises(ValueError, line_total, "ABC1234", "1", qty, "AUD")


def test_bad_inputs():
    raises(ValueError, line_total, "AB1234", "1", 1, "AUD")
    raises(ValueError, line_total, "ABC123", "1", 1, "AUD")
    raises(ValueError, line_total, "ABC1234", "1", 1, "EUR")
    raises(ValueError, line_total, "ABC1234", "abc", 1, "AUD")


def test_result_is_an_int():
    assert type(line_total("ABC1234", "2.50", 2, "AUD")) is int

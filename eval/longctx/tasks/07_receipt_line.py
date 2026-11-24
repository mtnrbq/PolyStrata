PROMPT = r'''
Add a function `receipt_line(sku: str, qty: int, line_minor: int, currency: str) -> str` to `shopkit/orders.py`. It
returns the SKU in the project's normal form, then ` x` and the quantity, then two spaces, then the line's amount
formatted exactly the way the project formats money everywhere else. For example,
`receipt_line(" abc-1234", 2, 123450, "AUD")` returns `"ABC1234 x2  AUD 1,234.50"`. Keep the other functions in
the file as they are.
'''
DEFAULT_FILE = "shopkit/orders.py"
REPLACE = {"shopkit/orders.py": "@orders_full.py"}

from datetime import date

from shopkit.orders import order_total, receipt_line


def test_the_example():
    assert receipt_line(" abc-1234", 2, 123450, "AUD") == "ABC1234 x2  AUD 1,234.50"


def test_zero_decimal_currency():
    assert receipt_line("XYZ98765", 1, 1235, "JPY") == "XYZ98765 x1  JPY 1,235"


def test_three_decimal_currency():
    assert receipt_line("XYZ98765", 3, 5, "BHD") == "XYZ98765 x3  BHD 0.005"


def test_negative_amount():
    assert receipt_line("XYZ98765", 1, -300, "AUD") == "XYZ98765 x1  -AUD 3.00"


def test_large_amount():
    assert receipt_line("XYZ98765", 24, 123456789, "USD") == "XYZ98765 x24  USD 1,234,567.89"


def test_bad_inputs():
    raises(ValueError, receipt_line, "AB12", 1, 100, "AUD")
    raises(ValueError, receipt_line, "ABC1234", 1, 100, "EUR")


def test_other_functions_kept():
    assert order_total(12345, "AU", [], date(2026, 11, 24), 1500) == 14874

PROMPT = r'''
Customers report that two orders can both reserve the last unit of an item, so the shop sells stock it does not have.
Find the cause and fix it.
'''
DEFAULT_FILE = "shopkit/stock.py"
REPLACE = {"shopkit/orders.py": "@orders_full.py"}
PATCHES = {"shopkit/stock.py": [("    if qty <= available(sku):", "    if qty <= _ON_HAND.get(sku, 0):")]}

from shopkit import stock


def test_last_unit_reserved_once():
    stock.set_stock("ABC1234", 1)
    assert stock.reserve("ABC1234", 1) is True
    assert stock.reserve("ABC1234", 1) is False
    assert stock.available("ABC1234") == 0


def test_partial_reservations():
    stock.set_stock("ABC1234", 5)
    assert stock.reserve("ABC1234", 3) is True
    assert stock.reserve("ABC1234", 3) is False
    assert stock.reserve("abc-1234", 2) is True
    assert stock.available("ABC1234") == 0


def test_release_makes_units_available_again():
    stock.set_stock("ABC1234", 1)
    assert stock.reserve("ABC1234", 1)
    stock.release("ABC1234", 1)
    assert stock.available("ABC1234") == 1 and stock.reserve("ABC1234", 1) is True


def test_failed_reservation_reserves_nothing():
    stock.set_stock("ABC1234", 2)
    assert stock.reserve("ABC1234", 3) is False
    assert stock.available("ABC1234") == 2


def test_bad_quantity():
    stock.set_stock("ABC1234", 2)
    raises(ValueError, stock.reserve, "ABC1234", 0)

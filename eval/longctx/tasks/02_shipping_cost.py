PROMPT = r'''
Implement `shipping_cost(weight_g, region)` in `shopkit/orders.py`. It returns the shipping price in AUD cents for a
parcel of `weight_g` grams going to `region`. Follow the shop's shipping rules exactly, including when shipping is not
possible, and raise `ValueError` in those cases.
'''
DEFAULT_FILE = "shopkit/orders.py"

from shopkit.orders import shipping_cost


def test_bands():
    assert [shipping_cost(w, "AU") for w in (1, 500, 501, 2000, 2001, 10000, 10001, 22000)] == \
        [895, 895, 1295, 1295, 2450, 2450, 4900, 4900]


def test_other_regions_pay_the_same():
    assert shipping_cost(800, "NZ") == 1295 and shipping_cost(800, "US-CA") == 1295


def test_too_heavy():
    raises(ValueError, shipping_cost, 22001, "AU")


def test_no_weight():
    raises(ValueError, shipping_cost, 0, "AU")
    raises(ValueError, shipping_cost, -5, "AU")


def test_region_that_is_not_shipped_to():
    raises(ValueError, shipping_cost, 100, "US-OR")

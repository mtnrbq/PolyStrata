"""Orders. Work in progress: each function below still has to be written."""


def line_total(sku: str, unit_price: str, qty: int, currency: str) -> int:
    raise NotImplementedError


def shipping_cost(weight_g: int, region: str) -> int:
    raise NotImplementedError


def order_total(goods: int, region: str, codes: list[str], today, weight_g: int) -> int:
    raise NotImplementedError

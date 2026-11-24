PROMPT = r'''
Write a function `parse_duration(s: str) -> int` that converts a duration string into a whole number of seconds.

- A duration is one or more parts. Each part is a non-negative integer followed by a unit: `d` (days), `h` (hours),
  `m` (minutes) or `s` (seconds). Examples: `"1h30m"`, `"45s"`, `"2d4h"`, `"1h 30m 15s"`.
- Parts may be separated by spaces. Leading and trailing whitespace is ignored.
- Each unit may appear at most once, and units must appear in the order d, h, m, s.
- Raise `ValueError` for anything else: an empty string, a number without a unit, a unit without a number, an unknown
  unit, a repeated or out-of-order unit, a sign, or a decimal point.
'''
from solution import parse_duration


def test_simple():
    assert parse_duration("45s") == 45
    assert parse_duration("1h30m") == 5400


def test_days():
    assert parse_duration("2d4h") == 187200
    assert parse_duration("100d") == 8640000


def test_spaces():
    assert parse_duration("1h 30m 15s") == 5415
    assert parse_duration("  5m  ") == 300


def test_zero():
    assert parse_duration("0s") == 0


def test_empty_is_an_error():
    for s in ("", "   "):
        raises(ValueError, parse_duration, s)


def test_malformed_is_an_error():
    for s in ("5", "h", "1x", "1.5h", "-1h", "+1h", "1h-", "1 h"):
        raises(ValueError, parse_duration, s)


def test_order_and_repeats_are_errors():
    for s in ("1m1h", "1h1h", "30s5m"):
        raises(ValueError, parse_duration, s)

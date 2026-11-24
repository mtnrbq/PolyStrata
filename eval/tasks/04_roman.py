PROMPT = r'''
Write two functions for Roman numerals:

- `to_roman(n: int) -> str` converts an integer from 1 to 3999 to standard uppercase Roman numerals, using the
  subtractive forms IV, IX, XL, XC, CD and CM. Raise `ValueError` for any other `n`.
- `from_roman(s: str) -> int` converts back. Accept only the canonical form that `to_roman` would produce: uppercase,
  and no forms such as "IIII", "IC", "VV" or "MMMM". Raise `ValueError` for anything else, including the empty string.
'''
from solution import from_roman, to_roman


def test_to_roman():
    assert [to_roman(n) for n in (1, 4, 9, 14, 40, 90, 400, 1994, 2024, 3999)] == \
        ["I", "IV", "IX", "XIV", "XL", "XC", "CD", "MCMXCIV", "MMXXIV", "MMMCMXCIX"]


def test_from_roman():
    assert from_roman("MCMXCIV") == 1994 and from_roman("III") == 3 and from_roman("MMMCMXCIX") == 3999


def test_round_trip_everything():
    assert all(from_roman(to_roman(n)) == n for n in range(1, 4000))


def test_to_roman_range():
    for n in (0, -1, 4000):
        raises(ValueError, to_roman, n)


def test_non_canonical_is_an_error():
    for s in ("", "IIII", "IC", "VV", "MMMM", "IIX", "XM", "iv", "ABC", "VX"):
        raises(ValueError, from_roman, s)

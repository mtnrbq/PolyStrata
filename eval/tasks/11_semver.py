PROMPT = r'''
Write a function `compare_versions(a: str, b: str) -> int` that compares two Semantic Versioning 2.0.0 version strings
by precedence. Return -1 if `a` comes first, 1 if `b` comes first, and 0 if they have the same precedence.

- A version is `MAJOR.MINOR.PATCH`, optionally followed by `-PRERELEASE` and then optionally by `+BUILD`.
- MAJOR, MINOR and PATCH are non-negative integers without leading zeros (`0` itself is fine) and are compared
  numerically, in that order.
- A version with a pre-release comes before the same version without one: `1.0.0-alpha` < `1.0.0`.
- Pre-releases are compared identifier by identifier (identifiers are separated by dots). Identifiers made only of
  digits are compared numerically and must not have leading zeros. Other identifiers are compared as ASCII strings.
  A numeric identifier comes before a non-numeric one. If all identifiers so far are equal, the pre-release with fewer
  identifiers comes first.
- Identifiers contain only `0-9`, `A-Z`, `a-z` and `-`, and are never empty. BUILD follows the same character rules
  and is ignored when comparing.
- Raise `ValueError` if either string is not a valid version.
'''
from solution import compare_versions

CHAIN = ["1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-alpha.beta", "1.0.0-beta", "1.0.0-beta.2", "1.0.0-beta.11",
         "1.0.0-rc.1", "1.0.0", "1.0.1", "1.2.0", "1.10.0", "2.0.0"]


def test_core_numbers():
    assert compare_versions("1.0.0", "2.0.0") == -1
    assert compare_versions("2.1.1", "2.1.0") == 1
    assert compare_versions("1.10.0", "1.9.0") == 1
    assert compare_versions("3.4.5", "3.4.5") == 0


def test_the_spec_chain():
    for i, a in enumerate(CHAIN):
        for j, b in enumerate(CHAIN):
            assert compare_versions(a, b) == (i > j) - (i < j), (a, b)


def test_build_is_ignored():
    assert compare_versions("1.0.0+build.5", "1.0.0") == 0
    assert compare_versions("1.0.0-rc.1+x", "1.0.0-rc.1+y") == 0
    assert compare_versions("1.0.0-rc.1+x", "1.0.0") == -1


def test_hyphens_in_identifiers():
    assert compare_versions("1.0.0-x-y", "1.0.0-x-z") == -1
    assert compare_versions("1.0.0-alpha-1", "1.0.0-alpha") == 1


def test_invalid():
    for bad in ("1.0", "1.0.0.0", "01.0.0", "1.00.0", "1.0.0-", "1.0.0-alpha..1", "1.0.0-01", "a.b.c",
                "1.0.0+", "1.0.0-al_pha", "", "v1.0.0"):
        raises(ValueError, compare_versions, bad, "1.0.0")
        raises(ValueError, compare_versions, "1.0.0", bad)

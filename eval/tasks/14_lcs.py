PROMPT = r'''
Write a function `lcs(a: str, b: str) -> str` that returns a longest common subsequence of two strings: the longest
string that can be obtained from both `a` and `b` by deleting characters, without reordering the rest. If there are
several of the same length, return any one of them. It must handle strings of 1,000 characters each in a few seconds.
'''
import random

from solution import lcs


def is_subsequence(s, t):
    it = iter(t)
    return all(ch in it for ch in s)


def check(a, b, length):
    got = lcs(a, b)
    assert len(got) == length, (got, length)
    assert is_subsequence(got, a) and is_subsequence(got, b), got


def test_small():
    check("ABCBDAB", "BDCABA", 4)
    check("AGGTAB", "GXTXAYB", 4)


def test_empty_and_disjoint():
    assert lcs("", "abc") == "" and lcs("abc", "") == ""
    assert lcs("abc", "xyz") == ""


def test_identical_and_contained():
    check("hello", "hello", 5)
    check("ace", "abcde", 3)


def length_dp(a, b):
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if x == y else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]


def test_random_against_dp():
    rng = random.Random(3)
    for _ in range(40):
        a = "".join(rng.choice("abc") for _ in range(rng.randint(0, 25)))
        b = "".join(rng.choice("abc") for _ in range(rng.randint(0, 25)))
        check(a, b, length_dp(a, b))


def test_long_strings():
    rng = random.Random(5)
    a = "".join(rng.choice("ACGT") for _ in range(1000))
    b = "".join(rng.choice("ACGT") for _ in range(1000))
    check(a, b, length_dp(a, b))

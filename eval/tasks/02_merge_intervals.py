PROMPT = r'''
Write a function `merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]`.

- Each interval `(a, b)` is closed: it covers every number from `a` to `b` inclusive. `a == b` is allowed.
- Merge intervals that overlap or touch, where one ends exactly where the next starts: `(1, 3)` and `(3, 5)` become
  `(1, 5)`. `(1, 2)` and `(3, 4)` do not touch and stay separate.
- The input may be in any order and must not be modified. Return the merged intervals sorted by start, as tuples.
- Raise `ValueError` if any interval has `a > b`.
'''
from solution import merge_intervals


def test_empty():
    assert merge_intervals([]) == []


def test_classic():
    assert merge_intervals([(1, 3), (2, 6), (8, 10), (15, 18)]) == [(1, 6), (8, 10), (15, 18)]


def test_touching_merge_but_neighbours_do_not():
    assert merge_intervals([(1, 3), (3, 5)]) == [(1, 5)]
    assert merge_intervals([(1, 2), (3, 4)]) == [(1, 2), (3, 4)]


def test_unsorted_and_nested():
    assert merge_intervals([(5, 6), (1, 2), (2, 3)]) == [(1, 3), (5, 6)]
    assert merge_intervals([(1, 10), (2, 3), (4, 5)]) == [(1, 10)]


def test_points_and_negatives():
    assert merge_intervals([(1, 1), (1, 1)]) == [(1, 1)]
    assert merge_intervals([(-5, -1), (-1, 0), (2, 2)]) == [(-5, 0), (2, 2)]


def test_input_not_modified():
    data = [(4, 5), (1, 3), (2, 4)]
    copy = list(data)
    merge_intervals(data)
    assert data == copy


def test_bad_interval():
    raises(ValueError, merge_intervals, [(1, 2), (3, 1)])

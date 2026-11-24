PROMPT = r'''
Write a function `spiral_order(matrix: list[list]) -> list` that returns the elements of a matrix in clockwise spiral
order, starting at the top-left corner and going right first.

- `[]` and `[[]]` (no elements) return `[]`.
- Raise `ValueError` if the rows do not all have the same length.
- Do not modify the argument.
'''
from solution import spiral_order


def test_square():
    assert spiral_order([[1, 2, 3], [4, 5, 6], [7, 8, 9]]) == [1, 2, 3, 6, 9, 8, 7, 4, 5]


def test_wide_and_tall():
    assert spiral_order([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]) == [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7]
    assert spiral_order([[1, 2], [3, 4], [5, 6], [7, 8]]) == [1, 2, 4, 6, 8, 7, 5, 3]


def test_single_row_and_column():
    assert spiral_order([[1, 2, 3]]) == [1, 2, 3]
    assert spiral_order([[1], [2], [3]]) == [1, 2, 3]
    assert spiral_order([[7]]) == [7]


def test_empty():
    assert spiral_order([]) == [] and spiral_order([[]]) == []


def test_every_element_once():
    m = [[r * 7 + c for c in range(7)] for r in range(5)]
    out = spiral_order(m)
    assert sorted(out) == list(range(35)) and out[:7] == list(range(7))


def test_ragged_is_an_error():
    raises(ValueError, spiral_order, [[1, 2], [3]])


def test_argument_not_modified():
    m = [[1, 2], [3, 4]]
    spiral_order(m)
    assert m == [[1, 2], [3, 4]]

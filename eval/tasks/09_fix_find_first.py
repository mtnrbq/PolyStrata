PROMPT = r'''
This function is meant to return the index of the first occurrence of `target` in the sorted list `items`, or -1 if
`target` is absent. It has bugs. Write a corrected version with the same name and signature. It must stay O(log n)
and must not use the `bisect` module.

```python
def find_first(items, target):
    """Return the index of the first occurrence of target in the sorted list items, or -1."""
    lo, hi = 0, len(items)
    while lo < hi:
        mid = (lo + hi) // 2
        if items[mid] < target:
            lo = mid
        else:
            hi = mid - 1
    if items[lo] == target:
        return lo
    return -1
```
'''
from solution import find_first


def test_empty():
    assert find_first([], 3) == -1


def test_single():
    assert find_first([3], 3) == 0 and find_first([3], 4) == -1 and find_first([3], 2) == -1


def test_duplicates_give_the_first():
    assert find_first([1, 2, 2, 2, 3], 2) == 1
    assert find_first([5, 5, 5, 5], 5) == 0


def test_ends():
    items = [1, 3, 5, 7, 9]
    assert find_first(items, 1) == 0 and find_first(items, 9) == 4


def test_absent_between_and_outside():
    items = [1, 3, 5, 7, 9]
    assert [find_first(items, t) for t in (0, 2, 4, 6, 8, 10)] == [-1] * 6


def test_every_position():
    items = sorted([i // 3 for i in range(300)])
    assert all(find_first(items, v) == 3 * v for v in range(100))


def test_large_list_is_fast():
    items = list(range(2_000_000))
    assert all(find_first(items, v) == v for v in range(0, 2_000_000, 1999))

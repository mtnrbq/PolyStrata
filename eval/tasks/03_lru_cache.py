PROMPT = r'''
Write a class `LRUCache`, a least-recently-used cache.

- `LRUCache(capacity: int)`: raise `ValueError` if `capacity < 1`.
- `get(key, default=None)`: return the key's value, or `default` if it is absent. A successful `get` makes the key
  the most recently used.
- `put(key, value)`: insert the key or update its value, and make it the most recently used. If the cache then holds
  more than `capacity` items, remove the least recently used one.
- `len(cache)` is the number of items, and `key in cache` tests membership without changing which key was used most
  recently.
- `get` and `put` must take O(1) time on average.
'''
from solution import LRUCache


def test_evicts_least_recently_used():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    assert "a" not in c and c.get("b") == 2 and c.get("c") == 3


def test_get_refreshes():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1
    c.put("c", 3)
    assert c.get("b") is None and c.get("a") == 1


def test_update_refreshes_and_does_not_grow():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 10)
    assert len(c) == 2
    c.put("c", 3)
    assert c.get("a") == 10 and "b" not in c


def test_contains_does_not_refresh():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert "a" in c
    c.put("c", 3)
    assert "a" not in c


def test_default_and_len():
    c = LRUCache(3)
    assert c.get("x", 42) == 42 and len(c) == 0
    c.put("x", 0)
    assert c.get("x", 42) == 0 and len(c) == 1


def test_capacity_one():
    c = LRUCache(1)
    c.put(1, "a")
    c.put(2, "b")
    assert len(c) == 1 and c.get(2) == "b" and c.get(1) is None


def test_bad_capacity():
    raises(ValueError, LRUCache, 0)


def test_many_operations_are_fast():
    c = LRUCache(1000)
    for i in range(200_000):
        c.put(i, i)
        c.get(i - 500)
    assert len(c) == 1000 and c.get(199_999) == 199_999

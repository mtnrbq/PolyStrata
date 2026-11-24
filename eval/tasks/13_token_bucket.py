PROMPT = r'''
Write a class `TokenBucket`, a rate limiter.

- `TokenBucket(rate: float, capacity: float, clock=time.monotonic)`: tokens are added at `rate` per second, up to
  `capacity`. The bucket starts full. `clock` is a function returning the current time in seconds; tests pass their
  own. Raise `ValueError` if `rate <= 0` or `capacity <= 0`.
- `allow(tokens: float = 1.0) -> bool`: first add the tokens earned since the last call (never more than `capacity`
  in total). Then, if at least `tokens` are available, remove them and return `True`; otherwise remove nothing and
  return `False`. Raise `ValueError` if `tokens <= 0` or `tokens > capacity`.
- `available() -> float` returns the number of tokens available now, after adding the tokens earned, without removing
  any.
'''
import math

from solution import TokenBucket


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def test_starts_full_then_empties():
    c = Clock()
    b = TokenBucket(1, 3, clock=c)
    assert [b.allow() for _ in range(4)] == [True, True, True, False]


def test_refills_over_time():
    c = Clock()
    b = TokenBucket(2, 4, clock=c)
    assert b.allow(4) and not b.allow()
    c.t += 0.5
    assert b.allow() and not b.allow()
    c.t += 1.0
    assert math.isclose(b.available(), 2)


def test_never_above_capacity():
    c = Clock()
    b = TokenBucket(10, 5, clock=c)
    c.t += 100
    assert math.isclose(b.available(), 5)
    assert b.allow(5) and not b.allow(0.5)


def test_failed_request_takes_nothing():
    c = Clock()
    b = TokenBucket(1, 5, clock=c)
    assert b.allow(4)
    assert not b.allow(2)
    assert math.isclose(b.available(), 1) and b.allow(1)


def test_fractional():
    c = Clock()
    b = TokenBucket(0.5, 1, clock=c)
    assert b.allow(1)
    c.t += 1
    assert not b.allow(1) and math.isclose(b.available(), 0.5)
    c.t += 1
    assert b.allow(1)


def test_errors():
    raises(ValueError, TokenBucket, 0, 1)
    raises(ValueError, TokenBucket, 1, 0)
    b = TokenBucket(1, 2, clock=Clock())
    raises(ValueError, b.allow, 0)
    raises(ValueError, b.allow, 3)

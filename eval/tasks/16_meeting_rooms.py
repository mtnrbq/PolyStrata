PROMPT = r'''
Write a function `min_meeting_rooms(meetings: list[tuple[int, int]]) -> int` that returns the smallest number of rooms
needed to hold all the meetings.

- Each meeting `(start, end)` is half-open: it uses a room from `start` up to, but not including, `end`. A meeting that
  ends at time t and one that starts at time t can share a room.
- The input may be in any order. An empty list needs 0 rooms.
- Raise `ValueError` if any meeting has `start >= end`.
- It must handle 100,000 meetings in well under a second.
'''
import random

from solution import min_meeting_rooms


def test_empty_and_single():
    assert min_meeting_rooms([]) == 0 and min_meeting_rooms([(1, 2)]) == 1


def test_classic():
    assert min_meeting_rooms([(0, 30), (5, 10), (15, 20)]) == 2
    assert min_meeting_rooms([(7, 10), (2, 4)]) == 1


def test_back_to_back_share_a_room():
    assert min_meeting_rooms([(1, 5), (5, 10), (10, 15)]) == 1


def test_all_overlapping():
    assert min_meeting_rooms([(1, 10)] * 4 + [(2, 3)]) == 5


def test_errors():
    raises(ValueError, min_meeting_rooms, [(1, 2), (3, 3)])
    raises(ValueError, min_meeting_rooms, [(5, 1)])


def test_random_against_brute_force():
    rng = random.Random(11)
    for _ in range(50):
        ms = []
        for _ in range(rng.randint(1, 15)):
            s = rng.randint(0, 30)
            ms.append((s, s + rng.randint(1, 10)))
        best = max(sum(s <= t < e for s, e in ms) for t in range(0, 45))
        assert min_meeting_rooms(ms) == best, ms


def test_large_input():
    rng = random.Random(2)
    ms = []
    for _ in range(100_000):
        s = rng.randint(0, 1_000_000)
        ms.append((s, s + rng.randint(1, 50)))
    assert min_meeting_rooms(ms) >= 1

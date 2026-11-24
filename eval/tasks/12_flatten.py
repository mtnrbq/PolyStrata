PROMPT = r'''
Write two functions for nested dictionaries whose keys are strings:

- `flatten(d: dict, sep: str = ".") -> dict` turns nested dictionaries into one level, joining the keys on the path
  with `sep`: `{"a": {"b": 1}}` becomes `{"a.b": 1}`. Values that are not dictionaries (lists included) are kept as
  they are. An empty nested dictionary is kept as a value: `{"a": {}}` stays `{"a": {}}`.
- `unflatten(d: dict, sep: str = ".") -> dict` does the reverse, splitting every key on `sep`.
  `unflatten(flatten(x)) == x` for any `x` whose keys do not contain `sep`.
- `unflatten` raises `ValueError` when two keys conflict, for example `{"a": 1, "a.b": 2}`, where `a` would have to be
  both a value and a dictionary.
- Neither function modifies its argument.
'''
import copy

from solution import flatten, unflatten

NESTED = {"a": 1, "b": {"c": 2, "d": {"e": [1, {"x": 1}], "f": None}}, "g": {}, "h": {"i": {}}}
FLAT = {"a": 1, "b.c": 2, "b.d.e": [1, {"x": 1}], "b.d.f": None, "g": {}, "h.i": {}}


def test_flatten():
    assert flatten(NESTED) == FLAT


def test_unflatten():
    assert unflatten(FLAT) == NESTED


def test_round_trip_and_empty():
    assert unflatten(flatten(NESTED)) == NESTED
    assert flatten({}) == {} and unflatten({}) == {}


def test_other_separator():
    assert flatten({"a": {"b": {"c": 1}}}, sep="/") == {"a/b/c": 1}
    assert unflatten({"a/b": 1, "a/c": 2}, sep="/") == {"a": {"b": 1, "c": 2}}


def test_conflicts():
    raises(ValueError, unflatten, {"a": 1, "a.b": 2})
    raises(ValueError, unflatten, {"a.b": 2, "a": 1})
    raises(ValueError, unflatten, {"a.b": 1, "a.b.c": 2})


def test_arguments_not_modified():
    n, f = copy.deepcopy(NESTED), copy.deepcopy(FLAT)
    flatten(n)
    unflatten(f)
    assert n == NESTED and f == FLAT

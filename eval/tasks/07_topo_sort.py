PROMPT = r'''
Write a function `topo_sort(deps: dict[str, list[str]]) -> list[str]` that orders nodes by their dependencies.

- `deps[x]` lists the nodes that `x` depends on. Each of them must come before `x` in the result.
- Every node appears exactly once in the result, including nodes that only appear in someone's dependency list.
  A dependency may be listed more than once.
- When several nodes could come next, take the alphabetically smallest, so the result is unique.
- Raise `ValueError` if the dependencies contain a cycle, including a node that depends on itself.
'''
from solution import topo_sort


def test_empty_and_simple():
    assert topo_sort({}) == []
    assert topo_sort({"b": ["a"]}) == ["a", "b"]


def test_chain():
    assert topo_sort({"c": ["a", "b"], "b": ["a"], "a": []}) == ["a", "b", "c"]


def test_ties_are_alphabetical():
    assert topo_sort({"z": [], "a": [], "m": []}) == ["a", "m", "z"]
    assert topo_sort({"d": ["b", "c"], "b": ["a"], "c": ["a"]}) == ["a", "b", "c", "d"]


def test_smallest_available_not_smallest_overall():
    assert topo_sort({"a": ["z"], "b": []}) == ["b", "z", "a"]


def test_repeated_dependency():
    assert topo_sort({"b": ["a", "a"]}) == ["a", "b"]


def test_cycles():
    raises(ValueError, topo_sort, {"a": ["b"], "b": ["a"]})
    raises(ValueError, topo_sort, {"a": ["a"]})
    raises(ValueError, topo_sort, {"a": ["b"], "b": ["c"], "c": ["a"], "d": []})


def test_larger_graph():
    deps = {f"n{i:04d}": [f"n{i - 1:04d}"] if i else [] for i in range(3000)}
    assert topo_sort(deps) == sorted(deps)

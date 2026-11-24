PROMPT = r'''
Write a function
`shortest_path(graph: dict[str, dict[str, float]], start: str, goal: str) -> tuple[float, list[str]] | None`.

- `graph[u][v] = w` is a directed edge from `u` to `v` with weight `w`. A node may appear only as a target, with no
  entry of its own in `graph`.
- Return `(total_cost, path)` for a cheapest path from `start` to `goal`, where `path` lists the nodes from `start` to
  `goal` inclusive. If several paths are equally cheap, return any one of them.
- If `start == goal`, return `(0, [start])`, even if `start` is not in `graph`. Return `None` if `goal` cannot be
  reached.
- Raise `ValueError` if any edge weight in `graph` is negative.
'''
import math
import random

from solution import shortest_path


def check(graph, start, goal, cost):
    got = shortest_path(graph, start, goal)
    assert got is not None, "no path returned"
    c, path = got
    assert math.isclose(c, cost), (c, cost)
    assert path[0] == start and path[-1] == goal, path
    assert math.isclose(sum(graph[a][b] for a, b in zip(path, path[1:])), cost), path


G = {"a": {"b": 1, "c": 4}, "b": {"c": 2, "d": 5}, "c": {"d": 1}, "d": {}}


def test_basic():
    check(G, "a", "d", 4)
    check(G, "b", "d", 3)


def test_same_node():
    assert shortest_path(G, "a", "a") == (0, ["a"])
    assert shortest_path({}, "x", "x") == (0, ["x"])


def test_unreachable():
    assert shortest_path(G, "d", "a") is None
    assert shortest_path(G, "a", "zzz") is None


def test_target_only_node_and_float_weights():
    check({"s": {"t": 0.5, "u": 0.2}, "u": {"t": 0.2}}, "s", "t", 0.4)


def test_zero_weights_and_ties():
    check({"a": {"b": 0, "c": 1}, "b": {"c": 1}}, "a", "c", 1)


def test_negative_weight():
    raises(ValueError, shortest_path, {"a": {"b": -1}}, "a", "b")


def test_random_graphs_against_floyd():
    rng = random.Random(7)
    for _ in range(30):
        n = 12
        g = {str(i): {} for i in range(n)}
        for _ in range(30):
            u, v = rng.randrange(n), rng.randrange(n)
            if u != v:
                g[str(u)][str(v)] = rng.randint(1, 20)
        d = [[0 if i == j else math.inf for j in range(n)] for i in range(n)]
        for u in g:
            for v, w in g[u].items():
                d[int(u)][int(v)] = min(d[int(u)][int(v)], w)
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    d[i][j] = min(d[i][j], d[i][k] + d[k][j])
        for _ in range(5):
            s, t = rng.randrange(n), rng.randrange(n)
            if d[s][t] == math.inf:
                assert shortest_path(g, str(s), str(t)) is None
            else:
                check(g, str(s), str(t), d[s][t])


def test_big_graph_is_fast():
    n = 20000
    g = {str(i): {str(i + 1): 1, str((i * 7) % n): 3} for i in range(n - 1)}
    c, path = shortest_path(g, "0", str(n - 1))
    assert c <= n - 1 and path[0] == "0" and path[-1] == str(n - 1)

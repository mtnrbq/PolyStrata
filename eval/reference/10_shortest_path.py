import heapq


def shortest_path(graph, start, goal):
    for u, es in graph.items():
        for v, w in es.items():
            if w < 0:
                raise ValueError((u, v, w))
    if start == goal:
        return (0, [start])
    dist, prev, heap = {start: 0}, {}, [(0, start)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        if u == goal:
            path = [u]
            while path[-1] != start:
                path.append(prev[path[-1]])
            return (d, path[::-1])
        for v, w in graph.get(u, {}).items():
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v], prev[v] = nd, u
                heapq.heappush(heap, (nd, v))
    return None

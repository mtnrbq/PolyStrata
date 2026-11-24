def flatten(d, sep="."):
    out = {}

    def walk(prefix, v):
        if isinstance(v, dict) and v:
            for k, x in v.items():
                walk(f"{prefix}{sep}{k}" if prefix else k, x)
        else:
            out[prefix] = v

    for k, v in d.items():
        walk(k, v)
    return out


def unflatten(d, sep="."):
    out = {}
    leaf = object()
    marks = {}
    for key, v in d.items():
        parts = key.split(sep)
        node, path = out, ()
        for p in parts[:-1]:
            path += (p,)
            if marks.get(path) is leaf:
                raise ValueError(key)
            marks[path] = dict
            node = node.setdefault(p, {})
        path += (parts[-1],)
        if path in marks:
            raise ValueError(key)
        marks[path] = leaf
        node[parts[-1]] = v
    return out

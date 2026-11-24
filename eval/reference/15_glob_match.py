def _compile(p):
    toks, i = [], 0
    while i < len(p):
        c = p[i]
        if c == "\\":
            if i + 1 >= len(p):
                raise ValueError("trailing backslash")
            toks.append(("lit", p[i + 1]))
            i += 2
        elif c == "*":
            toks.append(("star", None))
            i += 1
        elif c == "?":
            toks.append(("any", None))
            i += 1
        elif c == "[":
            j = i + 1
            neg = j < len(p) and p[j] == "!"
            if neg:
                j += 1
            items, first = [], True
            while True:
                if j >= len(p):
                    raise ValueError("unclosed [")
                if p[j] == "]" and not first:
                    break
                if j + 2 < len(p) and p[j + 1] == "-" and p[j + 2] != "]":
                    items.append((p[j], p[j + 2]))
                    j += 3
                else:
                    items.append((p[j], p[j]))
                    j += 1
                first = False
            toks.append(("set", (neg, items)))
            i = j + 1
        else:
            toks.append(("lit", c))
            i += 1
    return toks


def _one(tok, ch):
    kind, arg = tok
    if kind == "lit":
        return arg == ch
    if kind == "any":
        return True
    neg, items = arg
    return any(a <= ch <= b for a, b in items) != neg


def glob_match(pattern, text):
    toks = _compile(pattern)
    n = len(toks)
    # states: positions in toks reachable after reading a prefix of text
    def close(states):
        out, stack = set(states), list(states)
        while stack:
            s = stack.pop()
            if s < n and toks[s][0] == "star" and s + 1 not in out:
                out.add(s + 1)
                stack.append(s + 1)
        return out

    states = close({0})
    for ch in text:
        nxt = set()
        for s in states:
            if s < n:
                if toks[s][0] == "star":
                    nxt.add(s)
                elif _one(toks[s], ch):
                    nxt.add(s + 1)
        states = close(nxt)
        if not states:
            return False
    return n in states

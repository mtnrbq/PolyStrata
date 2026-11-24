import re

_TOK = re.compile(r"\s*(?:([0-9]+(?:\.[0-9]+)?)|(.))")


def evaluate(expr):
    toks, pos, s = [], 0, expr.rstrip()
    while pos < len(s):
        m = _TOK.match(s, pos)
        num, op = m.groups()
        if num is not None:
            toks.append(("n", float(num)))
        elif op in "+-*/()":
            toks.append(("o", op))
        else:
            raise ValueError(op)
        pos = m.end()
    i = 0

    def peek():
        return toks[i] if i < len(toks) else (None, None)

    def take():
        nonlocal i
        i += 1
        return toks[i - 1]

    def expr_():
        v = term()
        while peek() in (("o", "+"), ("o", "-")):
            op = take()[1]
            r = term()
            v = v + r if op == "+" else v - r
        return v

    def term():
        v = factor()
        while peek() in (("o", "*"), ("o", "/")):
            op = take()[1]
            r = factor()
            v = v * r if op == "*" else v / r
        return v

    def factor():
        k, t = peek()
        if (k, t) in (("o", "-"), ("o", "+")):
            take()
            v = factor()
            return -v if t == "-" else v
        if k == "n":
            return take()[1]
        if (k, t) == ("o", "("):
            take()
            v = expr_()
            if peek() != ("o", ")"):
                raise ValueError("missing )")
            take()
            return v
        raise ValueError(f"unexpected {t!r}")

    v = expr_()
    if i != len(toks):
        raise ValueError("trailing input")
    return float(v)

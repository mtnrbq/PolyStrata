def justify(text, width):
    if width < 1:
        raise ValueError(width)
    words = text.split()
    if any(len(w) > width for w in words):
        raise ValueError("word too long")
    lines, cur = [], []
    for w in words:
        if cur and sum(map(len, cur)) + len(cur) + len(w) > width:
            lines.append(cur)
            cur = []
        cur.append(w)
    if cur:
        lines.append(cur)
    out = []
    for i, line in enumerate(lines):
        if i == len(lines) - 1 or len(line) == 1:
            out.append(" ".join(line).ljust(width))
            continue
        spaces, gaps = width - sum(map(len, line)), len(line) - 1
        q, r = divmod(spaces, gaps)
        s = ""
        for j, w in enumerate(line[:-1]):
            s += w + " " * (q + (1 if j < r else 0))
        out.append(s + line[-1])
    return out

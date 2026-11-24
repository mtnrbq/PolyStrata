import re

_RE = re.compile(r"(?:([0-9]+)d)?\s*(?:([0-9]+)h)?\s*(?:([0-9]+)m)?\s*(?:([0-9]+)s)?")


def parse_duration(s: str) -> int:
    s = s.strip()
    m = _RE.fullmatch(s)
    if not s or not m or not any(m.groups()):
        raise ValueError(f"bad duration: {s!r}")
    return sum(int(g or 0) * k for g, k in zip(m.groups(), (86400, 3600, 60, 1)))

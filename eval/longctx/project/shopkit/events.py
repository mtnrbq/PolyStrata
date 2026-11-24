"""A tiny in-process event log. Every event name is 'noun.verb', in lower case."""

LOG = []


def emit(name: str, **payload):
    if name.count(".") != 1 or name != name.lower():
        raise ValueError(f"bad event name {name!r}")
    LOG.append((name, payload))


def clear():
    LOG.clear()

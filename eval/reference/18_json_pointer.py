import re

_INDEX = re.compile(r"0|[1-9][0-9]*")


def json_pointer_get(doc, pointer):
    if pointer == "":
        return doc
    if not pointer.startswith("/"):
        raise ValueError(pointer)
    for raw in pointer[1:].split("/"):
        if re.search(r"~(?![01])", raw):
            raise ValueError(raw)
        tok = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(doc, dict):
            if tok not in doc:
                raise KeyError(tok)
            doc = doc[tok]
        elif isinstance(doc, list):
            if not _INDEX.fullmatch(tok):
                raise ValueError(tok)
            i = int(tok)
            if i >= len(doc):
                raise KeyError(tok)
            doc = doc[i]
        else:
            raise KeyError(tok)
    return doc

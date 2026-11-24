PROMPT = r'''
Add a module `shopkit/report.py` with a function `known_events() -> list[str]`. It returns, sorted and without
duplicates, the name of every event the shopkit package can emit: every name passed to `emit` anywhere in shopkit.
Write the names out as literals; do not read or inspect source files at run time.
'''
DEFAULT_FILE = "shopkit/report.py"
REPLACE = {"shopkit/orders.py": "@orders_full.py"}

import re
from pathlib import Path


def test_the_names():
    from shopkit.report import known_events
    assert known_events() == ["code.accepted", "code.rejected", "stock.released", "stock.reserved", "stock.set",
                              "stock.short"]


def test_does_not_read_source_files():
    src = (Path(__file__).parent / "shopkit" / "report.py").read_text(encoding="utf-8")
    for pat in (r"\bopen\(", r"\bread_text\b", r"\bglob\b", r"\bwalk\b", r"\binspect\b", r"\bgetsource\b",
                r"\bimport ast\b", r"\bast\.", r"\blistdir\b", r"__file__", r"\bscandir\b", r"\biterdir\b"):
        assert not re.search(pat, src), pat

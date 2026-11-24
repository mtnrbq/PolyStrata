```python
# file: shopkit/report.py
"""What shopkit reports."""


def known_events() -> list[str]:
    return ["code.accepted", "code.rejected", "stock.released", "stock.reserved", "stock.set", "stock.short"]
```

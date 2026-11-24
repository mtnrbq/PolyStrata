PROMPT = r'''
Write a function `parse_csv_line(line: str, sep: str = ",") -> list[str]` that splits one line of CSV into fields,
without using the `csv` module.

- Fields are separated by `sep`, a single character. Unquoted fields are returned exactly as written: no trimming.
- A field is quoted when its first character is `"`. Inside a quoted field, `sep` is an ordinary character and `""`
  stands for one `"`. The quotes themselves are not part of the value.
- A `"` inside an unquoted field is an ordinary character.
- After a closing quote, the next character must be `sep` or the end of the line. Otherwise, or if a quote is never
  closed, raise `ValueError`.
- An empty line is one empty field: `[""]`.
'''
from solution import parse_csv_line


def test_plain():
    assert parse_csv_line("a,b,c") == ["a", "b", "c"]
    assert parse_csv_line(" a , b ") == [" a ", " b "]


def test_quoted_separator():
    assert parse_csv_line('a,"b,c",d') == ["a", "b,c", "d"]


def test_escaped_quotes():
    assert parse_csv_line('"he said ""hi""",x') == ['he said "hi"', "x"]
    assert parse_csv_line('""""') == ['"']


def test_empty_fields():
    assert parse_csv_line("") == [""]
    assert parse_csv_line(",") == ["", ""]
    assert parse_csv_line('a,,"",b') == ["a", "", "", "b"]


def test_quote_inside_unquoted_field():
    assert parse_csv_line('ab"c,d') == ['ab"c', "d"]


def test_other_separator():
    assert parse_csv_line('a;"b;c";d', sep=";") == ["a", "b;c", "d"]
    assert parse_csv_line("a,b;c", sep=";") == ["a,b", "c"]


def test_errors():
    raises(ValueError, parse_csv_line, '"abc')
    raises(ValueError, parse_csv_line, '"a"b,c')
    raises(ValueError, parse_csv_line, 'x,"a""')

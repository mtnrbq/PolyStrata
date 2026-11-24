PROMPT = r'''
Write a function `glob_match(pattern: str, text: str) -> bool` that tells whether the whole of `text` matches a glob
pattern. Do not use the `fnmatch`, `glob` or `re` modules.

- `*` matches any sequence of characters, including none. `?` matches exactly one character.
- `[abc]` matches one character from the set, `[a-z]` one from a range, and `[!abc]` or `[!a-z]` one character not in
  the set. Sets may mix single characters and ranges, as in `[a-cx]`. A `]` right after `[` or `[!` is a literal
  member of the set.
- A backslash makes the next character literal: `\*` matches only `*`. A backslash at the end of the pattern is an
  error.
- Raise `ValueError` for an error in the pattern, such as a `[` that is never closed.
- There is no special treatment of `/` or of a leading `.`.
- Matching must take polynomial time: a pattern such as `a*a*a*a*a*a*b` against a long run of `a`s must return
  quickly.
'''
from solution import glob_match


def test_literals_and_question_mark():
    assert glob_match("abc", "abc") and not glob_match("abc", "abd") and not glob_match("abc", "abcd")
    assert glob_match("a?c", "abc") and not glob_match("a?c", "ac")
    assert glob_match("", "") and not glob_match("", "a")


def test_star():
    assert glob_match("*", "") and glob_match("*", "anything")
    assert glob_match("a*c", "ac") and glob_match("a*c", "abbbc") and not glob_match("a*c", "abbbd")
    assert glob_match("*.py", "x.py") and not glob_match("*.py", "x.pyc")
    assert glob_match("**a", "bba") and glob_match("a*b*c", "a-b-b-c")


def test_sets_and_ranges():
    assert glob_match("[abc]", "b") and not glob_match("[abc]", "d")
    assert glob_match("x[a-c]y", "xby") and not glob_match("x[a-c]y", "xdy")
    assert glob_match("[a-cx]", "x") and glob_match("[0-9][0-9]", "42")


def test_negated_sets():
    assert glob_match("[!abc]", "d") and not glob_match("[!abc]", "a")
    assert glob_match("[!a-z]", "5") and not glob_match("[!a-z]", "q")


def test_bracket_as_member():
    assert glob_match("[]]", "]") and glob_match("[!]]", "a") and not glob_match("[!]]", "]")


def test_escapes():
    assert glob_match(r"\*", "*") and not glob_match(r"\*", "a")
    assert glob_match(r"a\?b", "a?b") and not glob_match(r"a\?b", "axb")
    assert glob_match(r"\[x]", "[x]")


def test_errors():
    raises(ValueError, glob_match, "[abc", "a")
    raises(ValueError, glob_match, "a\\", "a")


def test_no_exponential_backtracking():
    assert not glob_match("a*a*a*a*a*a*a*a*b", "a" * 60)
    assert glob_match("*a*b*c*d*e*", "x" * 300 + "abcde")

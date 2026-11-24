PROMPT = r'''
Write a function `evaluate(expr: str) -> float` that evaluates an arithmetic expression. Do not use `eval`, `exec`,
`compile` or the `ast` module.

- Numbers are non-negative integers or decimals such as `3`, `2.5` or `0.75`. Forms with a leading or trailing dot,
  such as `.5` or `5.`, need not be supported.
- Binary operators `+ - * /` have the usual precedence (`*` and `/` before `+` and `-`) and are all left-associative.
  `/` is true division.
- Unary minus and unary plus may repeat (`--1` is 1) and apply to the factor that follows: `2*-3` is -6, `-(1+2)` is
  -3.
- Parentheses may be used, and whitespace may appear between any tokens.
- Return the result as a float.
- Raise `ValueError` for malformed input: an empty expression, unbalanced or empty parentheses, a missing operand, two
  numbers in a row, or an unknown character. Raise `ZeroDivisionError` for division by zero.
'''
import math

from solution import evaluate

CASES = {"2+3*4": 14, "(2+3)*4": 20, "10/4": 2.5, "2-3-4": -5, "8/2/2": 2, "1.5*2": 3, " 7 ": 7, "2*-3": -6,
         "-(2+3)*2": -10, "--1": 1, "+4": 4, "((1))": 1, "1 - -1": 2, "3*(2+(4-1)*2)/4": 6, "0.75 * 4": 3}


def test_precedence_and_associativity():
    for e in ("2+3*4", "(2+3)*4", "10/4", "2-3-4", "8/2/2", "3*(2+(4-1)*2)/4"):
        assert math.isclose(evaluate(e), CASES[e]), e


def test_unary_operators():
    for e in ("2*-3", "-(2+3)*2", "--1", "+4", "1 - -1"):
        assert math.isclose(evaluate(e), CASES[e]), e


def test_numbers_and_spaces():
    for e in ("1.5*2", " 7 ", "((1))", "0.75 * 4"):
        assert math.isclose(evaluate(e), CASES[e]), e


def test_malformed_is_an_error():
    for e in ("", "1+", "(1", "1)", "2 3", "1+*2", "a", "()", "2(3)"):
        raises(ValueError, evaluate, e)


def test_division_by_zero():
    raises(ZeroDivisionError, evaluate, "1/0")
    raises(ZeroDivisionError, evaluate, "1/(2-2)")

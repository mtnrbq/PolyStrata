PROMPT = r'''
Write a function `justify(text: str, width: int) -> list[str]` that fully justifies text.

- Words are separated by any whitespace. Pack words greedily: put as many words as fit on each line, with at least
  one space between words.
- Every returned line is exactly `width` characters long.
- On every line except the last, spread the spaces between the words as evenly as possible. When they cannot be spread
  evenly, the gaps on the left get one more space than the gaps on the right. A line with a single word is
  left-aligned and padded with spaces on the right.
- The last line is left-aligned, with single spaces between words, and padded with spaces on the right.
- Text with no words returns `[]`. Raise `ValueError` if `width < 1` or a word is longer than `width`.
'''
from solution import justify


def test_example_one():
    assert justify("This is an example of text justification.", 16) == \
        ["This    is    an", "example  of text", "justification.  "]


def test_single_word_line_and_last_line():
    assert justify("What must be acknowledgment shall be", 16) == \
        ["What   must   be", "acknowledgment  ", "shall be        "]


def test_longer_text():
    text = "Science is what we understand well enough to explain to a computer. Art is everything else we do"
    assert justify(text, 20) == ["Science  is  what we", "understand      well", "enough to explain to",
                                 "a  computer.  Art is", "everything  else  we", "do                  "]


def test_no_words():
    assert justify("", 10) == [] and justify("  \n\t ", 10) == []


def test_exact_fit_and_whitespace():
    assert justify("hello", 5) == ["hello"]
    assert justify("a\nb\tc", 5) == ["a b c"]


def test_errors():
    raises(ValueError, justify, "toolongword", 5)
    raises(ValueError, justify, "a", 0)

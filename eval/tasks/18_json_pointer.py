PROMPT = r'''
Write a function `json_pointer_get(doc, pointer: str)` that resolves an RFC 6901 JSON Pointer against `doc`, a value
made of dicts, lists, strings, numbers, booleans and None.

- The empty pointer `""` refers to the whole document. Any other pointer must start with `/`, and each `/` starts a
  reference token.
- In a token, `~1` stands for `/` and `~0` for `~`. Decode `~1` before `~0`, so `~01` means `~1`. A `~` followed by
  anything other than `0` or `1` is an error.
- On a dict, the token is a key. On a list, the token must be `0` or a positive decimal integer without leading zeros,
  and it is an index. `-` is not a valid index here.
- Raise `ValueError` for a malformed pointer or an invalid list index token. Raise `KeyError` when a key is missing,
  an index is past the end of a list, or a token is applied to a value that is neither a dict nor a list.
'''
from solution import json_pointer_get

DOC = {"foo": ["bar", "baz"], "": 0, "a/b": 1, "c%d": 2, "e^f": 3, "g|h": 4, "i\\j": 5, "k\"l": 6, " ": 7,
       "m~n": 8, "nested": {"list": [{"x": [10, 20]}], "~1": "tilde-one"}}


def test_rfc_examples():
    assert json_pointer_get(DOC, "") is DOC
    assert json_pointer_get(DOC, "/foo") == ["bar", "baz"]
    assert json_pointer_get(DOC, "/foo/0") == "bar"
    assert json_pointer_get(DOC, "/") == 0
    assert json_pointer_get(DOC, "/a~1b") == 1
    assert [json_pointer_get(DOC, p) for p in ("/c%d", "/e^f", "/g|h", "/i\\j", "/k\"l", "/ ", "/m~0n")] == \
        [2, 3, 4, 5, 6, 7, 8]


def test_nested():
    assert json_pointer_get(DOC, "/nested/list/0/x/1") == 20


def test_decoding_order():
    assert json_pointer_get(DOC, "/nested/~01") == "tilde-one"


def test_falsy_values_are_found():
    assert json_pointer_get({"a": None, "b": False, "c": 0}, "/a") is None
    assert json_pointer_get({"a": None, "b": False, "c": 0}, "/b") is False


def test_malformed():
    for p in ("foo", "/foo/01", "/foo/-", "/foo/1.0", "/foo/+1", "/m~2n", "/x~"):
        raises(ValueError, json_pointer_get, DOC, p)


def test_missing():
    for p in ("/nope", "/foo/2", "/foo/0/x", "/nested/list/0/x/1/y"):
        raises(KeyError, json_pointer_get, DOC, p)

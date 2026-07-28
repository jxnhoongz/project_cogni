import pytest

from cogni import llm


def test_parse_json_plain():
    assert llm._parse_json('{"a": 1, "b": [2, 3]}', "m") == {"a": 1, "b": [2, 3]}


def test_parse_json_fenced():
    assert llm._parse_json('```json\n{"a": 1}\n```', "m") == {"a": 1}


def test_parse_json_repairs_trailing_comma_object():
    assert llm._parse_json('{"a": 1, "b": 2,}', "m") == {"a": 1, "b": 2}


def test_parse_json_repairs_trailing_comma_in_array():
    # the exact shape that aborted the 6-act script: a trailing comma before ]
    got = llm._parse_json('{"scenes": [{"narration": "x"}, {"narration": "y"},]}', "m")
    assert got == {"scenes": [{"narration": "x"}, {"narration": "y"}]}


def test_parse_json_strips_stray_control_char():
    assert llm._parse_json('{"a": "b\x07c"}', "m") == {"a": "bc"}


def test_parse_json_truly_broken_still_raises():
    with pytest.raises(RuntimeError, match="did not return valid JSON"):
        llm._parse_json('{"a": ', "m")

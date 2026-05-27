"""LLM client helpers — pure function tests (no network)."""

import pytest

from src.services.llm_clients import _parse_first_json_blob, prompt_hash


def test_prompt_hash_deterministic():
    a = prompt_hash("system", "user")
    b = prompt_hash("system", "user")
    assert a == b
    assert a.startswith("sha256:")


def test_prompt_hash_distinguishes_inputs():
    assert prompt_hash("a", "b") != prompt_hash("b", "a")
    assert prompt_hash("a", "b") != prompt_hash("ab", "")


def test_parse_first_json_blob_plain():
    assert _parse_first_json_blob('{"a": 1}') == {"a": 1}


def test_parse_first_json_blob_with_fence():
    text = '```json\n{"a": 1, "b": [2, 3]}\n```'
    assert _parse_first_json_blob(text) == {"a": 1, "b": [2, 3]}


def test_parse_first_json_blob_with_prose():
    text = 'Sure! Here is the JSON:\n{"a": 1}\nLet me know if you need more.'
    assert _parse_first_json_blob(text) == {"a": 1}


def test_parse_first_json_blob_raises_when_no_json():
    with pytest.raises(RuntimeError, match="No JSON object"):
        _parse_first_json_blob("hello world")

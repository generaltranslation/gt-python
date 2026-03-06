import json
import pathlib

import pytest
from generaltranslation._id import hash_source, hash_string, hash_template

FIXTURES = json.loads(
    (pathlib.Path(__file__).parent / "fixtures" / "id_fixtures.json").read_text()
)


@pytest.mark.parametrize("case", FIXTURES["hash_string"])
def test_hash_string(case):
    assert hash_string(case["input"]) == case["expected"]


@pytest.mark.parametrize("case", FIXTURES["hash_source"])
def test_hash_source(case):
    inp = case["input"]
    result = hash_source(
        inp["source"],
        context=inp.get("context"),
        id=inp.get("id"),
        max_chars=inp.get("maxChars"),
        data_format=inp.get("dataFormat", "ICU"),
    )
    assert result == case["expected"]


@pytest.mark.parametrize("case", FIXTURES["hash_template"])
def test_hash_template(case):
    assert hash_template(case["input"]) == case["expected"]


def test_hash_source_default_data_format_is_string():
    """Calling hash_source without data_format should use STRING (matching JS)."""
    expected = hash_source("hello", data_format="STRING")
    actual = hash_source("hello")
    assert actual == expected, (
        f"Default data_format should be STRING. "
        f"Got hash {actual} (expected {expected} for STRING)"
    )

"""Tests for format_cutoff and CutoffFormat."""

import json
from pathlib import Path

import pytest
from generaltranslation.formatting import CutoffFormat, format_cutoff

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "formatting_fixtures.json").read_text()
)


@pytest.mark.parametrize("case", FIXTURES["format_cutoff"])
def test_format_cutoff(case):
    result = format_cutoff(
        case["value"],
        locales=case.get("locales"),
        options=case.get("options"),
    )
    assert result == case["expected"], (
        f"format_cutoff({case['value']!r}, {case.get('locales')!r}, "
        f"{case.get('options')!r}): {result!r} != {case['expected']!r}"
    )


def test_cutoff_format_class():
    """Test CutoffFormat class directly."""
    fmt = CutoffFormat("en", {"max_chars": 5})
    assert fmt.format("Hello, world!") == "Hell\u2026"

    parts = fmt.format_to_parts("Hello, world!")
    assert parts == ["Hell", "\u2026"]

    opts = fmt.resolved_options()
    assert opts["max_chars"] == 5
    assert opts["style"] == "ellipsis"
    assert opts["terminator"] == "\u2026"


def test_cutoff_format_invalid_style():
    """Test that invalid style raises ValueError."""
    with pytest.raises(ValueError):
        CutoffFormat("en", {"max_chars": 5, "style": "invalid"})

import json
from pathlib import Path

import pytest

from generaltranslation.static import sanitize_var

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "static_fixtures.json").read_text()
)


@pytest.mark.parametrize(
    "case",
    FIXTURES["sanitize_var"],
    ids=[c["label"] for c in FIXTURES["sanitize_var"]],
)
def test_sanitize_var(case):
    result = sanitize_var(case["input"])
    assert result == case["expected"]

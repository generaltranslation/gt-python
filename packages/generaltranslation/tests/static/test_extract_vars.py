import json
from pathlib import Path
from typing import Any

import pytest
from generaltranslation.static import extract_vars

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "static_fixtures.json").read_text())


@pytest.mark.parametrize(
    "case",
    FIXTURES["extract_vars"],
    ids=[c["label"] for c in FIXTURES["extract_vars"]],
)
def test_extract_vars(case: dict[str, Any]) -> None:
    result = extract_vars(case["input"])
    assert result == case["expected"]

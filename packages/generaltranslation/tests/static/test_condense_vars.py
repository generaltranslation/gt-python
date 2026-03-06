import json
from pathlib import Path
from typing import Any

import pytest
from generaltranslation.static import condense_vars

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "static_fixtures.json").read_text())


@pytest.mark.parametrize(
    "case",
    FIXTURES["condense_vars"],
    ids=[c["label"] for c in FIXTURES["condense_vars"]],
)
def test_condense_vars(case: dict[str, Any]) -> None:
    result = condense_vars(case["input"])
    assert result == case["expected"]

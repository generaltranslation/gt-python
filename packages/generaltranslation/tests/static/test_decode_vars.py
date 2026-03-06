import json
from pathlib import Path

import pytest
from generaltranslation.static import decode_vars

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "static_fixtures.json").read_text()
)


@pytest.mark.parametrize(
    "case",
    FIXTURES["decode_vars"],
    ids=[c["label"] for c in FIXTURES["decode_vars"]],
)
def test_decode_vars(case):
    result = decode_vars(case["input"])
    assert result == case["expected"]

import json
from pathlib import Path

import pytest
from generaltranslation.static import index_vars

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "static_fixtures.json").read_text()
)


@pytest.mark.parametrize(
    "case",
    FIXTURES["index_vars"],
    ids=[c["label"] for c in FIXTURES["index_vars"]],
)
def test_index_vars(case):
    result = index_vars(case["input"])
    assert result == case["expected"]

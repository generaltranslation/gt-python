import json
from pathlib import Path

import pytest

from generaltranslation.static import declare_var

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "static_fixtures.json").read_text()
)


def _to_python_variable(v):
    """Convert JSON fixture variable to the Python type declareVar expects."""
    if v is None:
        return None
    return v


def _to_python_options(opts):
    """Convert JS ``{$name: ...}`` to Python ``name=...`` kwarg."""
    if not opts:
        return {}
    kwargs = {}
    if "$name" in opts:
        kwargs["name"] = opts["$name"]
    return kwargs


@pytest.mark.parametrize(
    "case",
    FIXTURES["declare_var"],
    ids=[c["label"] for c in FIXTURES["declare_var"]],
)
def test_declare_var(case):
    variable = _to_python_variable(case.get("variable"))
    kwargs = _to_python_options(case.get("options"))
    result = declare_var(variable, **kwargs)
    assert result == case["expected"]

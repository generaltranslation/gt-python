"""Tests for _get_locale_properties.py."""
import json
from pathlib import Path

import pytest
from generaltranslation.locales import get_locale_properties

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "locale_fixtures.json").read_text()
)

# Map camelCase fixture keys to snake_case dataclass fields
KEY_MAP = {
    "code": "code",
    "name": "name",
    "nativeName": "native_name",
    "maximizedCode": "maximized_code",
    "maximizedName": "maximized_name",
    "nativeMaximizedName": "native_maximized_name",
    "minimizedCode": "minimized_code",
    "minimizedName": "minimized_name",
    "nativeMinimizedName": "native_minimized_name",
    "languageCode": "language_code",
    "languageName": "language_name",
    "nativeLanguageName": "native_language_name",
    "nameWithRegionCode": "name_with_region_code",
    "nativeNameWithRegionCode": "native_name_with_region_code",
    "regionCode": "region_code",
    "regionName": "region_name",
    "nativeRegionName": "native_region_name",
    "scriptCode": "script_code",
    "scriptName": "script_name",
    "nativeScriptName": "native_script_name",
    "emoji": "emoji",
}


@pytest.mark.parametrize("case", FIXTURES["get_locale_properties"])
def test_get_locale_properties(case):
    result = get_locale_properties(
        case["locale"], default_locale=case["default_locale"]
    )
    expected = case["expected"]
    for camel_key, snake_key in KEY_MAP.items():
        if camel_key in expected:
            actual = getattr(result, snake_key)
            assert actual == expected[camel_key], (
                f"{snake_key}: {actual!r} != {expected[camel_key]!r}"
            )

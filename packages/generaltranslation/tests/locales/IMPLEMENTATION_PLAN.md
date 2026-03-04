# Plan: Implement Locale Functions + Tests

## Context

We have skeleton locale functions in the Python `generaltranslation` package that need implementation. The source of truth is the published `generaltranslation` npm package. JS-verified test fixtures are already saved at:

**`packages/generaltranslation/tests/locales/fixtures/locale_fixtures.json`**

**Dependency**: `babel` (not `langcodes`) for all locale operations. `minimize_locale` in `locales/utils/` is already implemented.

## Implementation Plan Per Function

### 1. `_custom_locale_mapping.py` — `get_custom_property`, `should_use_canonical_locale`

Pure dict lookups, no Babel needed.
- `get_custom_property`: If entry is a string, only `"name"` returns it. If dict, return `entry.get(property_name)`.
- `should_use_canonical_locale`: Check entry is a dict with `"code"` key whose value is a valid locale.

### 2. `_is_valid_locale.py` — `is_valid_locale`, `standardize_locale`, `_is_custom_language`

- `is_valid_locale`: `Locale.parse(locale, sep="-")` + validate components. Check custom mapping `"code"` redirect. Allow private-use `qaa`–`qtz`. Verify part count. Check language/region/script are known.
- `standardize_locale`: `Locale.parse()` then reconstruct with hyphens. Return original on failure. Note: underscored inputs (e.g. `en_us`) stay unchanged (matching JS behavior).
- `_is_custom_language`: `language >= "qaa" and language <= "qtz"`

### 3. `_get_locale_name.py` — `get_locale_name`

Check custom mapping first. Look up `Locale.parse(default_locale).languages[underscore_tag]` for compound CLDR names (e.g. "Austrian German"). Fall back to `Locale.parse(locale).get_display_name(default_locale)`.

### 4. `_get_locale_direction.py` — `get_locale_direction`

`Locale.parse(locale, sep="-").text_direction` — Babel has this built in. Return `"ltr"` on failure.

### 5. `_get_locale_emoji.py` — `get_locale_emoji`

Parse locale → check custom mapping → check region in `EMOJIS` → maximize to get likely region → check `EMOJI_EXCEPTIONS` for language → fallback to `DEFAULT_EMOJI`. Constants already defined in skeleton.

### 6. `_is_same_language.py` — `is_same_language`

Parse each locale with `Locale.parse()`, compare `.language`. Flatten list args. Return `False` on error.

### 7. `_is_same_dialect.py` — `is_same_dialect`

Parse each locale. Compare language. If both have region, regions must match. If both have script, scripts must match. Check all pairs. Return `False` on error.

### 8. `_is_superset_locale.py` — `is_superset_locale`

Parse both. Language must match. If super has region, must match sub's. If super has script, must match sub's. Return `False` on error.

### 9. `_requires_translation.py` — `requires_translation`

Validate all locales (return `False` if invalid). Return `False` if same dialect. If `approved_locales` given, return `False` if target language not represented. Otherwise `True`.

### 10. `_determine_locale.py` — `determine_locale`

Filter/standardize both lists. For each requested locale, find same-language candidates in approved, try exact/partial/minimized matching. Uses `get_locale_properties` for component extraction.

### 11. `_resolve_locale.py` — `resolve_canonical_locale`, `resolve_alias_locale`

Pure dict lookups. `resolve_canonical` returns `mapping[locale]["code"]` if applicable. `resolve_alias` builds a reverse index.

### 12. `_get_plural_form.py` — `get_plural_form`

Use `babel.plural.to_python(locale)` for CLDR rules. Layer overrides: `n==0` → `"zero"`, `|n|==1` → `"singular"/"one"`, `|n|==2` → `"dual"/"two"`. Then match CLDR result to available forms with fallback aliases.

### 13. `_get_locale_properties.py` — `get_locale_properties`

Use Babel `Locale.parse()` for components. Display names via `Locale.parse(display_locale).languages[tag]` for compound CLDR names, falling back to `get_display_name()`. Use `maximize_locale`/`minimize_locale` from utils. Use `get_locale_emoji` for emoji.

### 14. `_get_region_properties.py` — `get_region_properties`

Use `Locale("en", territory=region).territory_name` for name. Look up emoji from `EMOJIS` dict. Apply custom mapping overrides.

## Display Name Strategy

`Locale.parse(display_locale).languages[underscore_tag]` gives compound names matching JS exactly (e.g. "Austrian German", "American English"). Fall back to `get_display_name()` when no compound entry exists. Same for native names via `locale.languages[tag]`.

## Test File Structure (colocated)

```
packages/generaltranslation/tests/
├── __init__.py                       ← EXISTS
└── locales/
    ├── __init__.py                   ← EXISTS
    ├── fixtures/
    │   └── locale_fixtures.json      ← EXISTS (1410 lines, JS-verified)
    ├── test_custom_locale_mapping.py
    ├── test_is_valid_locale.py
    ├── test_get_locale_name.py
    ├── test_get_locale_direction.py
    ├── test_get_locale_emoji.py
    ├── test_is_same_language.py
    ├── test_is_same_dialect.py
    ├── test_is_superset_locale.py
    ├── test_requires_translation.py
    ├── test_determine_locale.py
    ├── test_resolve_locale.py
    ├── test_get_plural_form.py
    ├── test_get_locale_properties.py
    └── test_get_region_properties.py
```

Each test file loads fixtures directly from the JSON file and uses `pytest.mark.parametrize`.

## Verification

```bash
uv run pytest packages/generaltranslation/tests/locales/ -v
uv run ruff check packages/generaltranslation/
```

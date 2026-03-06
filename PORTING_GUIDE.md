# Porting Guide: `generaltranslation` JS → Python

## Overview

Port the JS `generaltranslation` core package (`/Users/ernestmccarter/Documents/dev/gt/packages/core/`) to Python at `/Users/ernestmccarter/Documents/dev/gt-python/packages/generaltranslation/`.

The Python package is already scaffolded with `pyproject.toml`, submodules, and a stub `GT` class. Dependencies: `httpx` (async HTTP), `babel` (locale/formatting), `generaltranslation-icu-messageformat-parser`, `generaltranslation-intl-messageformat`.

## Progress

| Module | Status | Tests | Notes |
|--------|--------|-------|-------|
| `locales/` | **Done** | 827 tests | 18 files, all functions ported |
| `formatting/` | **Done** | 160 tests | 9 files including `format_list_to_parts`, `CutoffFormat` |
| `static/` | **Done** | 164 tests | 10 files, all functions match JS output exactly |
| `_gt.py` | **Stub only** | — | Constructor with 4 params, no methods |
| `translate/` | **Not started** | — | Empty `__init__.py` |
| `errors/` | **Not started** | — | Empty `__init__.py` |
| `_id/` | **Not started** | — | Empty `__init__.py` |

**Total tests passing: 991**

## Python Package Structure

```
src/generaltranslation/
├── __init__.py          # Public API exports (currently only GT)
├── _gt.py               # GT class (main driver — stub)
├── py.typed             # PEP 561 marker
├── locales/             # ✅ Locale utilities (done)
├── formatting/          # ✅ Number, currency, datetime, list formatting (done)
├── static/              # ✅ GT variable encoding/decoding (done)
├── translate/           # ❌ API communication layer (not started)
├── errors/              # ❌ Error types (not started)
└── _id/                 # ❌ Hashing / ID generation (not started)
```

## JS → Python Dependency Mapping

| JS Dependency | Python Equivalent | Notes |
|---|---|---|
| `Intl.NumberFormat` | `babel.numbers` | `format_decimal`, `format_percent`, `format_currency` |
| `Intl.DateTimeFormat` | `babel.dates` | `format_date`, `format_time`, `format_datetime` |
| `Intl.PluralRules` | `babel.plural` | CLDR plural rules |
| `Intl.Locale` | `babel.Locale` | BCP 47 parsing, validation |
| `Intl.DisplayNames` | `babel.Locale.get_display_name()` | Language/region display names |
| `Intl.ListFormat` | `babel.lists.format_list()` | Available in Babel |
| `Intl.RelativeTimeFormat` | `babel.dates.format_timedelta()` | Relative time formatting |
| `@formatjs/icu-messageformat-parser` | `generaltranslation-icu-messageformat-parser` | **Separate workspace package, already complete** |
| `intl-messageformat` | `generaltranslation-intl-messageformat` | **Separate workspace package, already complete** |
| `crypto-js` (SHA256) | stdlib `hashlib.sha256` | Built-in, no dep needed |
| `fast-json-stable-stringify` | `json.dumps(obj, sort_keys=True)` | Built-in |
| `fetch` / HTTP | `httpx` | Already a dependency |

## What's Left to Port

### Tier 1: Core functionality

#### `errors/` module
Port from JS `src/errors.ts` + `src/logging/errors.ts`.

```python
class GTError(Exception):
    """Base error for GT operations."""

class ApiError(GTError):
    def __init__(self, error: str, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{error}: {message}")
```

#### `_id/` module
Port from JS `src/id.ts`. Hashing utilities for content identification.

```python
import hashlib, json

def hash_string(s: str) -> str:
    """SHA256, first 16 hex chars."""
    return hashlib.sha256(s.encode()).hexdigest()[:16]

def hash_source(source: dict, hash_function: Callable | None = None) -> str:
    """Hash source content with metadata. Uses json.dumps(sort_keys=True) for stable serialization."""

def hash_template(template: dict[str, str], hash_function: Callable | None = None) -> str:
    """Hash sorted JSON of template object."""
```

#### `translate/` module
Port from JS `src/translate/`. API communication using httpx.

```python
API_VERSION = "2026-02-18.v1"

def generate_request_headers(config: TranslationRequestConfig) -> dict[str, str]:
    """Headers: Content-Type, x-gt-project-id, x-gt-api-key, gt-api-version"""

async def api_request(config: TranslationRequestConfig, endpoint: str, body: dict | None = None, timeout: int = 60000, method: str = "POST", retry_policy: str = "exponential") -> dict:
    """HTTP request with retry logic. Exponential backoff: 500ms * 2^attempt. Max 3 retries on 5XX."""

async def translate_many(requests: list | dict, global_metadata: dict, config: TranslationRequestConfig, timeout: int | None = None) -> list | dict:
    """POST /v2/translate. Batch translation."""

async def upload_source_files(files: list, options: dict, config: TranslationRequestConfig) -> dict:
    """POST /v2/project/files/upload-files. Batch size: 100 files."""

async def enqueue_files(files: list, options: dict, config: TranslationRequestConfig) -> dict:
    """POST /v2/project/translations/enqueue."""

async def download_file_batch(batch: dict, config: TranslationRequestConfig) -> dict:
async def upload_translations(translations: dict, config: TranslationRequestConfig) -> dict:
async def setup_project(project_id: str, config: TranslationRequestConfig, options: dict) -> dict:
async def check_job_status(job_ids: list[str], config: TranslationRequestConfig, timeout_ms: int | None = None) -> dict:
```

#### GT class methods
Port from JS `src/index.ts`. The GT class should wrap all the standalone functions, binding its own config:

**Constructor** — needs additional params:
```python
class GT:
    def __init__(
        self,
        *,
        api_key: str = "",
        dev_api_key: str = "",
        project_id: str = "",
        base_url: str = "https://api.gtx.dev",
        source_locale: str = "en",
        target_locale: str = "",
        locales: list[str] | None = None,
        custom_mapping: dict[str, str] | None = None,
    ): ...
```

**Methods to implement:**
- Locale: `get_locale_name()`, `get_locale_emoji()`, `get_locale_properties()`, `get_locale_direction()`, `is_valid_locale()`, `determine_locale()`, `requires_translation()`, `is_same_language()`, `is_same_dialect()`, `is_superset_locale()`, `standardize_locale()`, `get_plural_form()`, `resolve_canonical_locale()`, `resolve_alias_locale()`, `get_region_properties()`
- Formatting: `format_num()`, `format_currency()`, `format_list()`, `format_list_to_parts()`, `format_date_time()`, `format_relative_time()`, `format_message()`, `format_cutoff()`
- Translation API: `translate_many()`, `setup_project()`, `enqueue_files()`, `download_file_batch()`, `upload_source_files()`, `upload_translations()`, `check_job_status()`, `query_branch_data()`, `create_branch()`, `get_project_data()`

### Tier 2: Nice to have

- `logging/` — Warning/error message helpers (could use stdlib `logging` directly)
- `settings/` — Constants like `LIBRARY_DEFAULT_LOCALE`, API URLs (can be inlined)

## Key Type Definitions

```python
from typing import TypedDict, Literal

DataFormat = Literal["JSX", "ICU", "I18NEXT", "STRING"]
LogLevel = Literal["debug", "info", "warn", "error", "off"]
PluralType = Literal["singular", "plural", "dual", "zero", "one", "two", "few", "many", "other"]

class TranslationRequestConfig(TypedDict):
    project_id: str
    base_url: str
    api_key: str

class EntryMetadata(TypedDict, total=False):
    id: str
    hash: str
    context: str
    max_chars: int
    data_format: DataFormat
```

## Settings / Constants

```python
LIBRARY_DEFAULT_LOCALE = "en"
DEFAULT_TIMEOUT = 60_000  # ms
DEFAULT_BASE_URL = "https://api.gtx.dev"
API_VERSION = "2026-02-18.v1"
PLURAL_FORMS = ["singular", "plural", "dual", "zero", "one", "two", "few", "many", "other"]
```

## Key Patterns to Follow

1. **Error handling**: Try/except with fallbacks. Log warnings instead of raising in non-critical locale functions.
2. **Retry logic**: Exponential backoff on 5XX (500ms * 2^attempt), max 3 retries. No retry on 4XX.
3. **Hashing**: SHA256, first 16 hex chars. Use `json.dumps(sort_keys=True)` for stable serialization.
4. **Async**: Translation/API functions should be `async` using `httpx.AsyncClient`.
5. **Naming**: Use `snake_case` for Python (JS uses `camelCase`). e.g. `getLocaleName` → `get_locale_name`.
6. **Logging**: Use Python's stdlib `logging` module. Create child loggers per module.

## Testing Strategy

Generate test fixtures by executing the **JS source functions** and writing results to JSON. Python tests consume these fixtures via `pytest.mark.parametrize`.

### Fixture Generation

Write a Node.js script for each module (e.g., `tests/formatting/fixtures/generate_fixtures.mjs`) that:
1. Imports the JS functions using `npx tsx` with dynamic `await import()` from the TS source files
2. Calls each function with a matrix of inputs (various locales, options, edge cases)
3. Writes the results to a JSON fixture file (e.g., `formatting_fixtures.json`)

This ensures the Python implementation produces **identical output** to the JS implementation.

**Important**: Use `await import(path)` for dynamic imports from the JS core TS source, NOT static `import ... from ...` which can fail with ESM/CJS issues. Run with `npx tsx`.

### Test Directory Layout

```
tests/
├── locales/
│   ├── fixtures/
│   │   └── locale_fixtures.json
│   └── test_*.py                       # 14 test files
├── formatting/
│   ├── fixtures/
│   │   ├── generate_fixtures.mjs
│   │   └── formatting_fixtures.json
│   └── test_*.py                       # 8 test files
└── static/
    ├── fixtures/
    │   ├── generate_fixtures.mjs
    │   └── static_fixtures.json
    ├── test_*.py                        # 6 test files
    └── test_known_discrepancies.py      # Edge case regression tests
```

## What NOT to Port

- JSX-specific types and processing (JsxElement, JsxChildren, etc.) — not relevant for Python
- Browser-specific code (btoa/atob — use stdlib `base64` instead)
- React/Next.js integration code
- SWC plugin
- `cache/` module — Python doesn't need Intl constructor caching
- `backwards-compatability/` module — legacy format conversion not needed for new Python package
- `utils/minify.ts` — code minification not relevant

## Lessons Learned

1. **Use Babel, not langcodes**: The actual implementation uses `babel` for all locale/formatting work. `langcodes` was the original plan but `babel` has better CLDR data coverage.

2. **ICU parser is a separate package**: The `generaltranslation-icu-messageformat-parser` and `generaltranslation-intl-messageformat` packages are workspace siblings, NOT inlined in the main package. They provide `Parser`, `print_ast`, and `IntlMessageFormat`.

3. **Parser/printer parity matters**: The Python ICU parser and printer must match `@formatjs/icu-messageformat-parser` behavior exactly, including:
   - `'<` and `'>` always trigger escape sequences (not just when `allow_tags=True`)
   - `print_ast` must re-escape `{}` via `printEscapedMessage` regex, `#` in plural context, and `'` at literal boundaries
   - Select/plural nodes use compact comma formatting (no spaces): `{name,select,...}`
   - Simple format nodes use spaced commas: `{name, type, style}`

4. **Boolean stringification**: Python `str(True)` → `"True"` but JS `String(true)` → `"true"`. `declare_var` handles this with `.lower()` for booleans.

5. **JS `undefined` in fixtures**: JS `undefined` is omitted from JSON. Test harnesses must use `.get("variable")` (defaulting to `None`) not `["variable"]`.

6. **`_find_other_span` in `index_vars`**: The Python parser doesn't store indices on individual option values (only on top-level nodes). `index_vars` uses manual brace-counting to find the `other` option's `{content}` span within a select node. This works correctly for all valid ICU input.

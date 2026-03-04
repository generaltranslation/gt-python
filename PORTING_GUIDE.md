# Porting Guide: `generaltranslation` JS → Python

## Overview

Port the JS `generaltranslation` core package (`/Users/ernestmccarter/Documents/dev/gt/packages/core/`) to Python at `/Users/ernestmccarter/Documents/dev/gt-python/packages/generaltranslation/`.

The Python package is already scaffolded with `pyproject.toml`, empty submodules, and a stub `GT` class. Dependencies: `httpx` (async HTTP), `langcodes` (locale utilities).

## Python Package Structure

```
src/generaltranslation/
├── __init__.py          # Public API exports
├── _gt.py               # GT class (main driver)
├── py.typed             # PEP 561 marker
├── locales/             # Locale utilities
├── formatting/          # Number, currency, datetime, list formatting
├── translate/           # API communication layer
├── errors/              # Error types
└── _id/                 # Hashing / ID generation
```

## JS → Python Dependency Mapping

| JS Dependency | Python Equivalent | Notes |
|---|---|---|
| `Intl.NumberFormat` | `langcodes` + stdlib `locale` | Or manual formatting |
| `Intl.DateTimeFormat` | stdlib `datetime.strftime` | |
| `Intl.PluralRules` | `langcodes` or manual CLDR rules | |
| `Intl.Locale` | `langcodes.Language` | BCP 47 parsing, validation |
| `Intl.DisplayNames` | `langcodes.Language.display_name()` | |
| `Intl.ListFormat` | Manual implementation | No stdlib equivalent |
| `Intl.RelativeTimeFormat` | Manual implementation | No stdlib equivalent |
| `intl-messageformat` | Port minimal ICU parser | ~300-500 lines, handle `{var}`, `{n, plural, ...}`, `{v, select, ...}` |
| `crypto-js` (SHA256) | stdlib `hashlib.sha256` | Built-in, no dep needed |
| `fast-json-stable-stringify` | `json.dumps(obj, sort_keys=True)` | Built-in |
| `fetch` / HTTP | `httpx` | Already a dependency |

## GT Class (main driver)

**JS constructor params:**
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

**Methods to implement on GT class:**
- Locale utilities: `get_locale_name()`, `get_locale_emoji()`, `get_locale_properties()`, `get_locale_direction()`, `is_valid_locale()`, `determine_locale()`, `requires_translation()`, `is_same_language()`, `is_same_dialect()`, `is_superset_locale()`, `standardize_locale()`, `get_plural_form()`
- Formatting: `format_num()`, `format_currency()`, `format_list()`, `format_date_time()`, `format_relative_time()`, `format_message()`, `format_cutoff()`
- Translation API: `translate_many()`, `setup_project()`, `enqueue_files()`, `download_file_batch()`, `upload_source_files()`, `upload_translations()`, `check_job_status()`

## Module Details

### `locales/`

**Key functions (all use `langcodes` internally):**

```python
def is_valid_locale(locale: str, custom_mapping: dict | None = None) -> bool:
    """BCP 47 validation. Supports private-use codes (qaa-qtz)."""

def get_locale_properties(locale: str, default_locale: str = "en", custom_mapping: dict | None = None) -> LocaleProperties:
    """Returns comprehensive locale metadata."""
    # LocaleProperties is a TypedDict or dataclass with:
    # code, name, native_name, language_code, language_name, native_language_name,
    # region_code, region_name, script_code, script_name, emoji, etc.

def get_locale_name(locale: str, display_locale: str = "en") -> str:
    """Get translated name for a locale. e.g. 'de' → 'German'"""

def get_locale_direction(locale: str) -> str:
    """Returns 'ltr' or 'rtl'."""

def get_locale_emoji(locale: str, custom_mapping: dict | None = None) -> str:
    """Flag emoji for locale's region."""

def determine_locale(locales: str | list[str], approved_locales: list[str], custom_mapping: dict | None = None) -> str | None:
    """Find best matching locale. Exact match → language match → fallback."""

def requires_translation(source_locale: str, target_locale: str, approved_locales: list[str] | None = None, custom_mapping: dict | None = None) -> bool:
    """Returns False if same dialect or no approved match."""

def is_same_language(*locales: str) -> bool:
def is_same_dialect(*locales: str) -> bool:
def is_superset_locale(super_locale: str, sub_locale: str) -> bool:
def standardize_locale(locale: str) -> str:

def get_plural_form(n: int | float, forms: list[str] | None = None, locales: list[str] | None = None) -> str:
    """Determine plural form. Forms: 'singular', 'plural', 'dual', 'zero', 'one', 'two', 'few', 'many', 'other'"""
```

### `formatting/`

**Functions wrapping locale-aware formatting:**

```python
def format_num(value: float, locales: str | list[str] | None = None, options: dict | None = None) -> str:
def format_currency(value: float, currency: str = "USD", locales: str | list[str] | None = None, options: dict | None = None) -> str:
def format_date_time(value: datetime, locales: str | list[str] | None = None, options: dict | None = None) -> str:
def format_list(value: list, locales: str | list[str] | None = None, options: dict | None = None) -> str:
def format_relative_time(value: int | float, unit: str, locales: str | list[str] | None = None, options: dict | None = None) -> str:
def format_message(message: str, locales: str | list[str] | None = None, variables: dict | None = None) -> str:
    """ICU MessageFormat. Handles {name}, {count, plural, one {# item} other {# items}}, {gender, select, ...}"""
def format_cutoff(value: str, locales: str | list[str] | None = None, options: dict | None = None) -> str:
```

### `translate/`

**API communication using httpx:**

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

### `errors/`

```python
class ApiError(Exception):
    def __init__(self, error: str, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{error}: {message}")
```

### `_id/`

**Hashing utilities:**

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

## Key Type Definitions

```python
from dataclasses import dataclass
from typing import TypedDict, Literal

DataFormat = Literal["JSX", "ICU", "I18NEXT", "STRING"]
LogLevel = Literal["debug", "info", "warn", "error", "off"]
PluralType = Literal["singular", "plural", "dual", "zero", "one", "two", "few", "many", "other"]

@dataclass
class LocaleProperties:
    code: str
    name: str
    native_name: str
    language_code: str
    language_name: str
    native_language_name: str
    region_code: str
    region_name: str
    native_region_name: str
    script_code: str
    script_name: str
    native_script_name: str
    emoji: str
    # ... etc

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
6. **Logging**: Use Python's stdlib `logging` module. Create child loggers per module. Default level from `_GT_LOG_LEVEL` env var.

## What NOT to Port

- JSX-specific types and processing (JsxElement, JsxChildren, etc.) — not relevant for Python
- Browser-specific code (btoa/atob — use stdlib `base64` instead)
- React/Next.js integration code
- SWC plugin
- IntlCache class (Python doesn't need this — no Intl constructors to cache)

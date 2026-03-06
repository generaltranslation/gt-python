# Plan: Python i18n Library (gt-i18n, gt-flask, gt-fastapi)

## Context

Porting the JS `gt-i18n` and `gt-node` packages to Python. The JS packages provide:
- `gt-i18n`: Core i18n manager, translation resolution, hashing, interpolation, fallbacks
- `gt-node`: Node.js AsyncLocalStorage adapter + `initializeGT()` + `withGT()` for Express/serverless

The Python equivalents will be:
- **gt-i18n**: Core logic (I18nManager, TranslationsManager, translation functions, `t()` internals)
- **gt-flask**: Thin Flask adapter (middleware hook, locale detection, re-exports `t()`)
- **gt-fastapi**: Thin FastAPI adapter (Starlette middleware, locale detection, re-exports `t()`)

The core `generaltranslation` Python package already has all foundational utilities: `hash_source`, `index_vars`, `format_message`, `extract_vars`, `condense_vars`, `decode_vars`, `declare_var`, `format_cutoff`, locale utilities, and `IntlMessageFormat`.

## Decisions

- **`t()` is the primary function name** (standard i18n convention)
- **`t_fallback()`** — a standalone function that does interpolation only (no locale lookup, no translation resolution). Mirrors JS `gtFallback()`.
- **Separate packages**: gt-flask and gt-fastapi are thin adapters; gt-i18n holds all logic
- **`ContextVarStorageAdapter` is the default** in gt-i18n — Flask/FastAPI adapters don't need to create their own. It uses Python's `contextvars.ContextVar` which works for both threaded (Flask) and async (FastAPI) contexts.
- **Translation loading**: Configurable — eager at startup (default) or lazy per-locale
- **Custom translation loader**: Users can override the remote CDN loader with a custom `load_translations` callback (e.g., read from local JSON files)
- **Locale detection**: Accept-Language header by default + user-provided custom `get_locale` callback
- **Use `uv init` CLI** to scaffold gt-fastapi package (not by hand)

---

## Package 1: gt-i18n

### File Structure

```
packages/gt-i18n/src/gt_i18n/
├── __init__.py                              # Public exports
├── _config.py                               # I18nConfig TypedDict + defaults
├── i18n_manager/
│   ├── __init__.py                          # Re-exports
│   ├── _storage_adapter.py                  # Abstract StorageAdapter base class
│   ├── _context_var_adapter.py              # ContextVar-based StorageAdapter
│   ├── _translations_manager.py             # Translation cache + loader
│   ├── _remote_loader.py                    # CDN translation loader (httpx)
│   ├── _i18n_manager.py                     # I18nManager class
│   └── _singleton.py                        # Module-level get/set singleton
├── translation_functions/
│   ├── __init__.py                          # Re-exports
│   ├── _hash_message.py                     # hashMessage (index_vars + hash_source)
│   ├── _extract_variables.py                # Filter $-prefixed keys from options
│   ├── _interpolate.py                      # Interpolate translated ICU string
│   ├── _t.py                                # t() function implementation
│   ├── _fallbacks.py                        # t_fallback(), m_fallback()
│   ├── _msg.py                              # msg() — register message with hash
│   └── _decode.py                           # decode_msg, decode_options (base64)
```

### Key Components

#### StorageAdapter (`_storage_adapter.py`)
Port of `StorageAdapter.ts`. Abstract base class.
```python
class StorageAdapter(ABC):
    @abstractmethod
    def get_item(self, key: str) -> str | None: ...
    @abstractmethod
    def set_item(self, key: str, value: str) -> None: ...
```

#### ContextVarStorageAdapter (`_context_var_adapter.py`)
**Default adapter** used by I18nManager when no custom adapter is provided. Uses Python's `contextvars.ContextVar` — equivalent of Node's `AsyncLocalStorage`. Works for both threaded (Flask) and async (FastAPI) contexts. Each request automatically gets its own context. Flask and FastAPI adapter packages do NOT need to create their own — they just call `initialize_gt()` which uses this default.
```python
_locale_var: contextvars.ContextVar[str] = contextvars.ContextVar("gt_locale")

class ContextVarStorageAdapter(StorageAdapter):
    def get_item(self, key): return _locale_var.get(None) if key == "locale" else None
    def set_item(self, key, value): _locale_var.set(value) if key == "locale"
```

#### TranslationsManager (`_translations_manager.py`)
Port of `TranslationsManager.ts`. Caches `dict[str, str]` (hash → translated string) per locale with configurable expiry.
- `async get_translations(locale) -> dict[str, str]` — loads if not cached
- `get_translations_sync(locale) -> dict[str, str]` — returns cached (empty if not loaded)
- `async load_all(locales: list[str])` — eagerly fetch all locales

#### Remote Loader (`_remote_loader.py`)
Port of `createRemoteTranslationLoader`. Fetches from CDN via httpx.
- URL pattern: `{cache_url}/{project_id}/{locale}`
- Returns `dict[str, str]`

#### I18nManager (`_i18n_manager.py`)
Port of `I18nManager.ts`. Central orchestrator.
```python
class I18nManager:
    def __init__(
        self, *,
        default_locale: str = "en",
        locales: list[str] | None = None,
        project_id: str | None = None,
        cache_url: str | None = None,
        store_adapter: StorageAdapter | None = None,  # defaults to ContextVarStorageAdapter
        load_translations: TranslationsLoader | None = None,  # custom loader overrides remote CDN
        cache_expiry_time: int = 60_000,
        ...
    ): ...
    def get_locale(self) -> str          # reads from store_adapter
    def set_locale(self, locale: str)    # writes to store_adapter
    def requires_translation(self, locale=None) -> bool
    async def get_translations(self, locale=None) -> dict[str, str]
    def get_translations_sync(self, locale=None) -> dict[str, str]
    async def load_all_translations(self) -> None
```
- If `store_adapter` is None, creates a `ContextVarStorageAdapter` by default
- If `load_translations` is provided, uses it instead of the remote CDN loader
- Common custom loader: reading from local JSON files

#### Singleton (`_singleton.py`)
Module-level `_manager: I18nManager | None` with `get_i18n_manager()` / `set_i18n_manager()`.

#### hash_message (`_hash_message.py`)
```python
def hash_message(message: str, *, context=None, id=None, max_chars=None) -> str:
    return hash_source(index_vars(message), context=context, id=id, max_chars=max_chars, data_format="ICU")
```
Reuses: `generaltranslation._id.hash_source`, `generaltranslation.static.index_vars`

#### extract_variables (`_extract_variables.py`)
Filters `$`-prefixed GT keys from options dict, returning only user interpolation variables.

#### interpolate_message (`_interpolate.py`)
Port of `interpolateMessage.ts`. Applies `extract_vars` + `condense_vars` + `format_message` with fallback cascade.
Reuses: `generaltranslation.formatting.format_message`, `generaltranslation.formatting.format_cutoff`, `generaltranslation.static.extract_vars`, `generaltranslation.static.condense_vars`

#### t() function (`_t.py`)
The core user-facing function. Synchronous.
```python
def t(message: str, **kwargs) -> str:
    manager = get_i18n_manager()
    locale = manager.get_locale()
    if not manager.requires_translation(locale):
        return interpolate_message(message, kwargs)  # source locale, just interpolate
    translations = manager.get_translations_sync(locale)
    h = hash_message(message, context=kwargs.get("$context"), id=kwargs.get("$id"), max_chars=kwargs.get("$max_chars"))
    translated = translations.get(h)
    if translated:
        return interpolate_message(translated, {**kwargs, "$_fallback": message})
    return interpolate_message(message, kwargs)  # no translation found, use source
```

#### t_fallback (`_fallbacks.py`)
Standalone interpolation-only function. No locale lookup, no translation resolution. Mirrors JS `gtFallback()`. Useful for fallback rendering or when the user just wants variable interpolation without the full translation pipeline.
```python
def t_fallback(message: str, **kwargs) -> str:
    """Interpolate variables into message without translation lookup.

    Performs: extract_variables -> extract_vars -> condense_vars -> format_message -> format_cutoff
    Falls back to source message on any error.
    """
    return interpolate_message(message, kwargs)
```

#### msg / decode / m_fallback
- `msg()` — registers message, encodes hash+source as base64 suffix
- `decode_msg()` / `decode_options()` — extracts from encoded string
- `m_fallback()` — fallback for encoded messages (decodes then delegates to `t_fallback`)

---

## Package 2: gt-flask (thin adapter)

### File Structure
```
packages/gt-flask/src/gt_flask/
├── __init__.py                # Exports: initialize_gt, t
└── _setup.py                  # initialize_gt(), before_request hook, t re-export
```

### Key Components

#### initialize_gt (`_setup.py`)
```python
def initialize_gt(app: Flask, *, default_locale="en", locales=None, project_id=None,
                  cache_url=None, get_locale=None, load_translations=None, **kwargs):
    # No adapter creation needed — I18nManager defaults to ContextVarStorageAdapter
    manager = I18nManager(default_locale=default_locale, locales=locales,
                          project_id=project_id, load_translations=load_translations, ...)
    set_i18n_manager(manager)
    # Eager loading (default) — uses asyncio.run() at startup
    if kwargs.get("eager_loading", True):
        asyncio.run(manager.load_all_translations())

    @app.before_request
    def _set_locale():
        if get_locale:
            locale = get_locale(request)  # user callback
        else:
            locale = _detect_from_accept_language(request, manager)
        manager.set_locale(locale)
```

#### t re-export
```python
from gt_i18n import t  # just re-export
```

#### Locale detection
Default: parse `Accept-Language` header, resolve against `manager.get_locales()` using `generaltranslation.locales.determine_locale`. User can override with `get_locale` callback.

---

## Package 3: gt-fastapi (thin adapter)

### Scaffolding
Run `uv init packages/gt-fastapi --package` to create the package, then configure pyproject.toml.

### File Structure
```
packages/gt-fastapi/src/gt_fastapi/
├── __init__.py                # Exports: initialize_gt, t
└── _setup.py                  # initialize_gt(), Starlette middleware, t re-export
```

### Key Components

#### initialize_gt (`_setup.py`)
```python
def initialize_gt(app: FastAPI, *, default_locale="en", locales=None, project_id=None,
                  cache_url=None, get_locale=None, load_translations=None, **kwargs):
    # No adapter creation needed — I18nManager defaults to ContextVarStorageAdapter
    manager = I18nManager(default_locale=default_locale, locales=locales,
                          project_id=project_id, load_translations=load_translations, ...)
    set_i18n_manager(manager)

    @app.on_event("startup")  # or lifespan
    async def _load_translations():
        if kwargs.get("eager_loading", True):
            await manager.load_all_translations()

    @app.middleware("http")
    async def gt_middleware(request: Request, call_next):
        if get_locale:
            locale = get_locale(request)
        else:
            locale = _detect_from_accept_language(request, manager)
        manager.set_locale(locale)
        return await call_next(request)
```

FastAPI advantage: can use `await` directly for eager loading in the startup event.

#### t re-export
```python
from gt_i18n import t
```

---

## Reusable Functions (already in generaltranslation core)

| Function | Location | Used For |
|---|---|---|
| `hash_source()` | `generaltranslation._id._hash` | Content hashing |
| `index_vars()` | `generaltranslation.static.index_vars` | Normalize _gt_ indices before hashing |
| `format_message()` | `generaltranslation.formatting.format_message` | ICU interpolation |
| `format_cutoff()` | `generaltranslation.formatting.format_cutoff` | Max chars truncation |
| `extract_vars()` | `generaltranslation.static.extract_vars` | Extract declared variables from ICU |
| `condense_vars()` | `generaltranslation.static.condense_vars` | Simplify _gt_ selects to refs |
| `decode_vars()` | `generaltranslation.static.decode_vars` | Replace _gt_ selects with values |
| `declare_var()` | `generaltranslation.static.declare_var` | Mark non-translatable content |
| `determine_locale()` | `generaltranslation.locales` | Resolve locale against approved list |
| `is_same_dialect()` | `generaltranslation.locales` | Check if translation needed |

---

## Implementation Order

1. **gt-i18n: StorageAdapter + ContextVarStorageAdapter**
2. **gt-i18n: TranslationsManager + remote loader**
3. **gt-i18n: I18nManager + singleton**
4. **gt-i18n: hash_message, extract_variables, interpolate_message**
5. **gt-i18n: t() function**
6. **gt-i18n: msg, decode, fallbacks**
7. **gt-i18n: __init__.py exports**
8. **Scaffold gt-fastapi** via `uv init packages/gt-fastapi --package`
9. **gt-flask: _setup.py** (initialize_gt + before_request + re-export t)
10. **gt-fastapi: _setup.py** (initialize_gt + middleware + re-export t)
11. **Tests**

---

## Verification & Testing

### Test Structure
```
packages/gt-i18n/tests/
├── test_hash_message.py           # hash_message parity with JS
├── test_extract_variables.py      # $-key filtering
├── test_interpolate.py            # interpolation pipeline + fallback cascade
├── test_t.py                      # t() with mock translations
├── test_t_fallback.py             # t_fallback() interpolation-only
├── test_msg.py                    # msg() encoding/decoding roundtrip
├── test_fallbacks.py              # m_fallback() with encoded messages
├── test_storage_adapter.py        # ContextVarStorageAdapter get/set/threading
├── test_translations_manager.py   # Cache hit/miss, expiry, custom loader
├── test_i18n_manager.py           # Full manager lifecycle
└── fixtures/
    └── generate_fixtures.mjs      # Generate JS reference data for parity tests

packages/gt-flask/tests/
├── test_flask_integration.py      # Flask app with before_request middleware

packages/gt-fastapi/tests/
├── test_fastapi_integration.py    # FastAPI app with Starlette middleware
```

### Unit Tests (gt-i18n)

**hash_message parity** (`test_hash_message.py`):
- Generate JS fixtures using `hashMessage()` from gt-i18n JS
- Verify Python `hash_message()` produces identical hashes for same inputs
- Test with: plain messages, messages with `$context`, `$id`, `$max_chars`, messages with `declare_var` variables

**interpolate_message** (`test_interpolate.py`):
- Simple variable substitution: `"Hello, {name}!"` + `{name: "Alice"}` -> `"Hello, Alice!"`
- With declared variables (`_gt_` selects): extract + condense + format
- Fallback cascade: invalid translation falls back to source message
- `$max_chars` truncation via `format_cutoff`

**t() function** (`test_t.py`):
- Mock I18nManager with pre-loaded translations
- Source locale (no translation needed) -> returns interpolated source
- Target locale with matching translation -> returns interpolated translation
- Target locale with missing translation -> returns interpolated source (fallback)
- Variable interpolation through the full pipeline

**t_fallback()** (`test_t_fallback.py`):
- Pure interpolation, no manager/locale involved
- `t_fallback("Hello, {name}!", name="World")` -> `"Hello, World!"`
- With declared variables
- Error handling: bad ICU syntax -> returns source message

**msg() roundtrip** (`test_msg.py`):
- `msg("Hello, {name}!", name="Alice")` -> encoded string
- `decode_msg(encoded)` -> `"Hello, Alice"`
- `decode_options(encoded)` -> `{"$_source": "Hello, {name}!", "$_hash": "...", "name": "Alice"}`

**ContextVarStorageAdapter** (`test_storage_adapter.py`):
- Set/get locale within same context
- Isolation: different threads/tasks get independent values
- Default (no value set) returns None

**TranslationsManager** (`test_translations_manager.py`):
- Custom loader returning known translations -> verify cache hit
- Cache expiry: after expiry time, loader is called again
- `load_all()`: all configured locales loaded eagerly
- `get_translations_sync()`: returns cached data or empty dict
- Error in loader -> returns empty dict, doesn't crash

### Integration Tests

**Flask** (`test_flask_integration.py`):
```python
def test_flask_t_with_accept_language():
    app = Flask(__name__)
    initialize_gt(app, default_locale="en", locales=["en", "es"],
                  load_translations=lambda locale: {"<hash>": "Hola, mundo!"} if locale == "es" else {})

    @app.route("/hello")
    def hello():
        return {"message": t("Hello, world!")}

    with app.test_client() as client:
        # Spanish
        resp = client.get("/hello", headers={"Accept-Language": "es"})
        assert resp.json["message"] == "Hola, mundo!"
        # English (source locale, no translation needed)
        resp = client.get("/hello", headers={"Accept-Language": "en"})
        assert resp.json["message"] == "Hello, world!"
```

**FastAPI** (`test_fastapi_integration.py`):
```python
def test_fastapi_t_with_accept_language():
    app = FastAPI()
    initialize_gt(app, default_locale="en", locales=["en", "es"],
                  load_translations=lambda locale: {"<hash>": "Hola, mundo!"} if locale == "es" else {})

    @app.get("/hello")
    def hello():
        return {"message": t("Hello, world!")}

    with TestClient(app) as client:
        resp = client.get("/hello", headers={"Accept-Language": "es"})
        assert resp.json()["message"] == "Hola, mundo!"
```

**Custom locale callback** test:
- Pass `get_locale=lambda req: "fr"` -> always uses French

**Custom translation loader** test:
- Pass `load_translations` that reads from a JSON file -> verify translations load correctly

### Running Tests
```bash
uv run pytest packages/gt-i18n/tests -v
uv run pytest packages/gt-flask/tests -v
uv run pytest packages/gt-fastapi/tests -v
# All at once:
uv run pytest packages/gt-i18n packages/gt-flask packages/gt-fastapi -v
```

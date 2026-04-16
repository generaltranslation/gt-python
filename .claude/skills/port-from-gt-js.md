---
name: port-from-gt-js
description: Style guide for porting features from the gt (JavaScript) monorepo to this gt-python repo. Use whenever you touch Python packages that mirror a JS counterpart — the JS repo is the source of truth and Python trails it, so new work in Python should match existing JS semantics while conforming to Python idioms.
user-invocable: true
allowed-tools: Agent, Bash, Read, Write, Edit, Glob, Grep, TaskCreate, TaskUpdate
---

# Porting from `gt` (JS) → `gt-python`

The JS monorepo at `~/Documents/dev/gt` is the **canonical implementation**. `gt-python` trails it. When you port a feature you are translating semantics faithfully; when you design a new feature here, you still match JS conventions unless there is a Python-specific reason not to.

## Read this first

Before touching code, pull up the corresponding JS package side-by-side. The package map is small and stable:

| gt (JS)                                         | gt-python                                                         | Notes                                                                        |
| ----------------------------------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `packages/core` (`generaltranslation`)          | `packages/generaltranslation`                                     | Core toolkit: `GT` class, locales, formatting, translate API client, hashing |
| `packages/i18n` (`gt-i18n`)                     | `packages/gt-i18n`                                                | Runtime `I18nManager`, `t()` / `msg()`, storage adapters, loaders            |
| `packages/supported-locales`                    | `packages/generaltranslation-supported-locales`                   | Static locale registry                                                       |
| — (bundled into `generaltranslation`)           | `packages/generaltranslation-intl-messageformat` + `...-icu-messageformat-parser` | Python splits the ICU/formatter libs out; JS uses `intl-messageformat` + `@formatjs/icu-messageformat-parser` as deps inside core |
| `packages/next` / `packages/react` / `packages/node` | `packages/gt-fastapi` / `packages/gt-flask`                     | Different frameworks, same shape: provider + middleware + manager singleton  |
| `packages/cli`, `packages/compiler`, `packages/python-extractor` | — (no counterpart)                                   | Extraction + build-time rewriting lives in the JS CLI; don't reinvent it here |

The JS side has source extraction (Babel/SWC/compiler) and the `gt` CLI; Python **intentionally** does not. Python code is discovered by the JS CLI's `@generaltranslation/python-extractor` (tree-sitter-python). Don't build a Python extractor or CLI unless the user explicitly asks.

## Naming conventions — the translation table

Apply these mechanically first, then read the code to catch exceptions.

| JS                                  | Python                                           |
| ----------------------------------- | ------------------------------------------------ |
| `camelCase` function                | `snake_case` function                            |
| `PascalCase` class / type           | `PascalCase` class / `TypedDict` / `dataclass`   |
| `camelCase.ts` file                 | `_snake_case.py` file (leading underscore marks module-private) |
| `const libraryDefaultLocale`        | `LIBRARY_DEFAULT_LOCALE` (module-level UPPER_SNAKE for public constants) |
| TS `interface` / `type`             | `TypedDict` (for API shapes) or `@dataclass` (for value objects) |
| Interface in `types.ts`             | `TypedDict` in `_types.py`                       |
| `./internal` subpath export         | `<pkg>.internal` submodule                       |
| `./types` subpath export            | Re-export from `__init__.py`, or `<pkg>.X` submodule |
| `./errors` subpath export           | `<pkg>.errors` submodule                         |

### Concrete identifier map (spot-check)

These are representative, not exhaustive — confirm when porting.

| JS                        | Python                       |
| ------------------------- | ---------------------------- |
| `class GT`                | `class GT`                   |
| `class I18nManager`       | `class I18nManager`          |
| `class ApiError`          | `class ApiError`             |
| `new GT({ sourceLocale, targetLocale })` | `GT(source_locale=..., target_locale=...)` |
| `gt.queryBranchData(q)`   | `await gt.query_branch_data(q)` |
| `gt.translateMany(...)`   | `await gt.translate_many(...)` |
| `hashSource`              | `hash_source`                |
| `standardizeLocale`       | `standardize_locale`         |
| `getLocaleProperties`     | `get_locale_properties`      |
| `isValidLocale`           | `is_valid_locale`            |
| `requiresTranslation`     | `requires_translation`       |
| `invalidLocaleError(...)` | `invalid_locale_error(...)`  |
| `$context` / `$id` / `$maxChars` user option | `_context` / `_id` / `_max_chars` user kwarg (Python has no `$`) |

### The `_prefix` convention — two different meanings

- **JS `_foo`** (e.g. `_translateMany`, `_standardizeLocale`) marks an internal implementation re-imported into the public barrel. The barrel then exposes it without the underscore as a method on `GT`.
- **Python `_foo.py`** marks a module-private file inside a package. The function *inside* that file has no underscore. When the `GT` class imports it, it aliases with `as _translate_many`:

  ```python
  # packages/generaltranslation/src/generaltranslation/_gt.py
  from generaltranslation.translate import translate_many as _translate_many
  ```

  This mirrors the JS pattern and keeps class internals shadow-free.

## Options, kwargs, and wire format

This is the trickiest area — Python is Pythonic outside, JS-compatible on the wire.

1. **Public Python APIs** take keyword-only arguments (`*, ...`) using `snake_case`. See `GT.__init__`.
2. **"Options dicts"** (second-class JS-style config bags) exist where they mirror a JS signature that takes `options`. Python accepts **both** `snake_case` and `camelCase` keys in those dicts for interop — see `GT.enqueue_files` and `GT.download_file` which check both `source_locale`/`sourceLocale` and `file_id`/`fileId`.
3. **HTTP request bodies** are always `camelCase` — the API is the JS API. See `translate_many()` in `translate/_translate.py` building `{ "targetLocale", "sourceLocale", "metadata" }`.
4. **HTTP response bodies** are `camelCase`. Don't rename fields into snake_case in the returned dict; keep wire shape intact so callers see the same shape as the JS SDK returns. The GT class re-maps `locale` fields through `resolve_alias_locale` but preserves the surrounding keys.

When porting a new method: accept both cases in the options dict, build the body in camelCase, return whatever the API returns unchanged (plus whatever locale-alias remapping the JS side does).

## Types: TypedDict vs dataclass vs Pydantic

- **`TypedDict`** for anything that crosses the wire or mirrors a JS `interface` (e.g. `TranslationResult`, `JobStatusEntry`, `TranslateOptions`). Default location: `_types.py` inside the submodule.
- **`@dataclass`** for value objects with behavior/defaults (e.g. `LocaleProperties` — 19 fields defaulting to `""`).
- **`Literal[...]`** for enum-like unions (e.g. `PluralType`, `RetryPolicy`).
- **Type aliases** for wire shapes that are just dicts: `CustomMapping = dict[str, str | dict[str, str]]`.
- **Do NOT use Pydantic.** The core deliberately avoids it. Babel is the i18n backend; validation is manual.

Annotate everything — `mypy` is configured with `disallow_untyped_defs = true`.

## Errors

Both repos use the same two-layer pattern:

1. A **custom exception** for external failures: JS `ApiError` / Python `ApiError` (in `generaltranslation.errors._api_error`).
2. **Error message factories** — functions returning pre-formatted strings: JS `invalidLocaleError(locale)` → Python `invalid_locale_error(locale)`. Collected in `errors/_messages.py`.

Validation failures in public methods use `ValueError(error_message_factory(...))`; HTTP failures use `ApiError`. Don't invent new exception types unless the JS side has a new one.

## Async, HTTP, retries

- **`httpx.AsyncClient`** is the HTTP client. Never switch to `requests`.
- Core methods are `async def`. The `GT` class exposes them as `async`. Formatting and locale utilities are sync (same as JS).
- Retry policy mirrors JS: `"exponential" | "linear" | "none"`, `MAX_RETRIES = 3`, `INITIAL_DELAY_MS = 500`. See `translate/_request.py` — `api_request()` is the one place retries happen; do not reimplement per-endpoint.
- Timeouts are **always in milliseconds** at the public API boundary (matches JS); convert to seconds right at the `httpx` call site (`timeout_s = timeout_ms / 1000.0`).
- `asyncio.sleep()` between retries. `asyncio.TimeoutError` / `httpx.TimeoutException` are distinct — wrap both.

## Framework integrations

Don't invent a new shape — both `gt-fastapi` and `gt-flask` already exemplify it:

- Single entry point `initialize_gt(app, *, default_locale=None, locales=None, project_id=None, ..., get_locale=None, load_translations=None, eager_loading=True, config_path=None, load_config=None) -> I18nManager`.
- Calls `set_i18n_manager(manager)` for singleton access.
- Registers middleware / `before_request` hook to detect locale per request (default: `Accept-Language`).
- Eager-loads translations on startup when `eager_loading=True`:
  - FastAPI: async lifespan context manager.
  - Flask: `asyncio.run(manager.load_all_translations())` as a sync-to-async bridge.
- Reads config from `gt.config.json` via `load_gt_config()` — CLI flags (JS side) have no Python equivalent, so file config + explicit kwargs are the only sources.

If you add a new framework (e.g. Django, Starlette), copy the shape from `gt-flask/_setup.py` or `gt-fastapi/_setup.py` and vary only the locale-detection hook and lifespan mechanism.

## Package layout (per-package)

```
packages/<name>/
├── pyproject.toml                # project + uv build + workspace sources
├── README.md
├── src/<module_name>/            # snake_case module name
│   ├── __init__.py               # public API re-exports + __all__
│   ├── py.typed                  # PEP 561 marker (MUST exist)
│   ├── _gt.py / _foo.py          # private modules (leading underscore)
│   └── <submodule>/
│       ├── __init__.py           # submodule re-exports
│       ├── _types.py             # TypedDicts
│       └── _impl.py
└── tests/                        # pytest, NOT __tests__
    ├── <submodule>/
    │   └── test_foo.py
    └── conftest.py
```

- **Module name** uses underscores: `gt-i18n` package → `gt_i18n` module (Python identifiers can't contain hyphens).
- **Workspace dep** between packages goes through `[tool.uv.sources]` with `{ workspace = true }`. Don't use relative paths.
- **`py.typed`** must exist in every shippable package.
- **`__init__.py`** declares `__all__` explicitly — treat it like the JS barrel file.

## Testing

- `pytest` + `pytest-asyncio` (already in dev-deps). `@pytest.mark.asyncio` on async tests.
- Test files: `test_*.py` in `tests/`. Test classes: `class TestFoo:`. Test functions: `def test_bar(...)`.
- Use `monkeypatch` for env vars (`GT_API_KEY`, `GT_PROJECT_ID`).
- Do **not** collocate tests next to source (that's the JS convention). Use the `tests/` folder per package.
- For HTTP, mock `httpx.AsyncClient` rather than patching `api_request` — tests should cover the retry/error paths.

## Tooling & commands

- `make check` — full gate (lint + format + typecheck + test). Run before declaring work done.
- `make lint` / `make format` — Ruff only; line length 120; rules `E,F,I,N,W,UP`.
- `make typecheck` — mypy strict (`disallow_untyped_defs`).
- `make test` — pytest across all packages.
- `uv run pytest packages/<name>/` — targeted test run.
- `make changeset` (`sampo add`) — for any user-visible change; pick the affected packages and bump type.

## Porting workflow (when asked to port feature X from gt)

1. **Locate the JS source.** Find the matching file(s) in `~/Documents/dev/gt/packages/<pkg>/src`. Read them fully. Note: public signature, internal helpers, types, error messages, tests.
2. **Locate the Python target.** Find the matching Python package under `packages/`. If it doesn't exist yet, stop and confirm with the user before creating a new package.
3. **Check for drift.** Is the existing Python already partially ported? Compare `__init__.py` exports on both sides. Note what's missing.
4. **Translate names** via the tables above. `camelCase` → `snake_case`, `_internal.ts` → `_internal.py`, interfaces → `TypedDict`.
5. **Translate logic.** Keep control flow identical where possible. Replace `fetch` → `httpx`, `Promise.all` → `asyncio.gather`, `Object.fromEntries` → dict comprehension, `?.` → `.get()` / explicit `if` checks, `...spread` → `{**a, **b}`.
6. **Wire format untouched.** Request/response bodies stay `camelCase`. Accept both cases in incoming options dicts.
7. **Mirror errors.** Same validation conditions, same messages — use the Python error-message factories, adding new ones in `errors/_messages.py` if the JS side has one that doesn't exist yet.
8. **Tests.** Port the JS tests to `tests/` with pytest-style assertions. Tests that rely on JSX / TS-only behaviors don't port — skip and note it.
9. **Re-export.** Add new public symbols to `__init__.py` and `__all__`. If the JS side exposes them via a subpath (`/internal`, `/types`), add them to the corresponding Python submodule's `__init__.py`.
10. **Changeset.** `sampo add`, pick affected packages, choose bump type. The `gt-python` release process depends on this.

## Known deliberate divergences

Not every difference is a bug. The following are intentional and should be preserved:

- **No Python CLI / compiler / extractor-in-repo.** The JS CLI drives extraction across both ecosystems.
- **Python ships ICU/formatter as separate workspace packages** (`generaltranslation-intl-messageformat`, `...-icu-messageformat-parser`) because there's no pure-Python `intl-messageformat` on PyPI to depend on.
- **`_context` / `_id` / `_max_chars` (underscore prefix)** instead of JS's `$context` / `$id` / `$maxChars` — `$` is not a valid Python identifier character.
- **`StorageAdapter` / `ContextVarStorageAdapter`** — Python's equivalent of JS's `FallbackStorageAdapter` (which uses `AsyncLocalStorage`). Python uses `contextvars`.
- **Flask integration uses `asyncio.run()`** as a sync/async bridge during startup — required because Flask is sync. Don't "fix" this to async-everywhere.
- **`babel` (the Python lib)** is a core dependency for CLDR data / number formatting / plurals. Unrelated to the JS Babel compiler.

## Quick reference: where things live

- Public API barrel: `packages/<pkg>/src/<mod>/__init__.py`
- Error messages: `packages/generaltranslation/src/generaltranslation/errors/_messages.py`
- HTTP client + retries: `packages/generaltranslation/src/generaltranslation/translate/_request.py`
- `GT` class: `packages/generaltranslation/src/generaltranslation/_gt.py`
- `I18nManager`: `packages/gt-i18n/src/gt_i18n/i18n_manager/_i18n_manager.py`
- `t()` / `msg()`: `packages/gt-i18n/src/gt_i18n/translation_functions/_t.py` / `_msg.py`
- Framework setup reference: `packages/gt-fastapi/src/gt_fastapi/_setup.py`, `packages/gt-flask/src/gt_flask/_setup.py`
- Settings / defaults: `packages/generaltranslation/src/generaltranslation/_settings.py`

When in doubt: read the JS file, then read an already-ported Python neighbour, then write code that matches both.

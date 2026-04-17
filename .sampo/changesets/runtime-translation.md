---
pypi/generaltranslation: patch
pypi/gt-i18n: minor
pypi/gt-fastapi: minor
pypi/gt-flask: minor
---

feat: add runtime translation system (ports gt PR #1207 / #1217)

- **gt-i18n**: new public async `tx()` for runtime string translation via `GT.translate_many`. Replaces `TranslationsManager` with a two-level cache hierarchy (`LocalesCache` → `TranslationsCache`) with batching, in-flight dedup, and a configurable concurrency cap. Adds new `I18nManager` methods (`lookup_translation`, `lookup_translation_with_fallback`, `load_translations`, `get_lookup_translation`) plus `lifecycle`, `batch_size`, `batch_interval_ms`, `max_concurrent_requests`, and `translation_timeout_ms` constructor kwargs. `hash_message` now accepts `format="ICU" | "STRING" | "I18NEXT"` and only applies `index_vars()` for ICU — subtle breaking change for any pre-existing STRING/I18NEXT cache keys. Deprecates `get_translations`, `get_translation_resolver`, `resolve_translation_sync`, and `get_translation_loader` with `DeprecationWarning`.
- **gt-fastapi / gt-flask**: `initialize_gt()` gains `lifecycle`, `batch_size`, `batch_interval_ms`, `max_concurrent_requests`, and `translation_timeout_ms` kwargs (all forwarded to `I18nManager`). Both packages now re-export `tx`.
- **generaltranslation**: `hash_source` and `hash_template` now pass `ensure_ascii=False` to `json.dumps`, matching JS `JSON.stringify` semantics for non-ASCII content. Fixes a cross-SDK hash divergence for messages and contexts containing unicode.

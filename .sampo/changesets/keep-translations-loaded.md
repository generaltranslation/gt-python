---
pypi/gt-i18n: patch
---

fix: keep translations loaded after the 60 s cache expiry (serve the cached copy while one background reload runs, keep it when a reload fails), default the CDN URL to cdn.gtx.dev and add the pinned `version_id` and `branch_id` to CDN requests, treat an empty `cache_url` as no CDN loading, and require generaltranslation 0.1.0 and generaltranslation-supported-locales 0.0.6 or later

---
pypi/gt-fastapi: patch
pypi/gt-flask: patch
---

fix: load each configured locale on its first request, eager-load `gt.config.json` locales in Flask, pass the `_branchId` from `gt.config.json` to the CDN loader, treat `cacheUrl: null` as no CDN loading, and require gt-i18n 0.3.1 and generaltranslation 0.1.0 or later

# Custom locale detection with `get_locale`

## Overview

Both `gt_fastapi` and `gt_flask` accept a `get_locale` callback in `initialize_gt()` that controls how the user's locale is determined on each request. If you don't provide one, the default behavior parses the `Accept-Language` header.

## Default behavior

When no `get_locale` is provided, GT automatically:

1. Reads the `Accept-Language` HTTP header from the incoming request (e.g. `en-US,en;q=0.9,es;q=0.8`)
2. Parses it into a list of locales sorted by quality value
3. Calls `determine_locale()` to find the best match against your configured `locales`
4. Falls back to `default_locale` if no match is found

This means out of the box, users get content in whatever language their browser requests — as long as you have translations for it.

## Providing a custom `get_locale`

Pass a callable that takes the request object and returns a locale string:

### FastAPI

```python
from fastapi import FastAPI, Request
from gt_fastapi import initialize_gt

app = FastAPI()

def get_locale(request: Request) -> str:
    """Detect locale from a query parameter, cookie, or header."""
    # 1. Check query parameter
    locale = request.query_params.get("lang")
    if locale:
        return locale

    # 2. Check cookie
    locale = request.cookies.get("locale")
    if locale:
        return locale

    # 3. Fall back to default
    return "en"

initialize_gt(
    app,
    default_locale="en",
    locales=["es", "fr"],
    get_locale=get_locale,
)
```

### Flask

```python
from flask import Flask, request
from gt_flask import initialize_gt

app = Flask(__name__)

def get_locale(req) -> str:
    """Detect locale from a query parameter, cookie, or header."""
    # 1. Check query parameter
    locale = req.args.get("lang")
    if locale:
        return locale

    # 2. Check cookie
    locale = req.cookies.get("locale")
    if locale:
        return locale

    # 3. Fall back to default
    return "en"

initialize_gt(
    app,
    default_locale="en",
    locales=["es", "fr"],
    get_locale=get_locale,
)
```

## How it's used internally

When a request comes in:

- **FastAPI**: The `gt_middleware` runs on every request. If `get_locale` is provided, it calls `get_locale(request)`. Otherwise it parses `Accept-Language`.
- **Flask**: A `before_request` hook runs on every request with the same logic.

The resolved locale is then set on the `I18nManager`, which `t()` reads from when translating strings.

## Common patterns

### URL path prefix

```python
def get_locale(request) -> str:
    """Extract locale from URL path like /es/about or /fr/home."""
    parts = request.url.path.strip("/").split("/")
    if parts and parts[0] in ("es", "fr", "de"):
        return parts[0]
    return "en"
```

### User profile / database

```python
def get_locale(request) -> str:
    """Look up locale from authenticated user's profile."""
    user = get_current_user(request)  # your auth logic
    if user and user.preferred_locale:
        return user.preferred_locale
    return "en"
```

### Subdomain

```python
def get_locale(request) -> str:
    """Detect locale from subdomain like es.example.com."""
    host = request.headers.get("host", "")
    subdomain = host.split(".")[0]
    if subdomain in ("es", "fr", "de"):
        return subdomain
    return "en"
```

## Notes

- Your `get_locale` function should always return a valid locale string
- If it returns a locale you don't have translations for, `t()` will fall back to the original (default locale) content
- The function receives the raw request object — `Request` for FastAPI, `flask.request` for Flask

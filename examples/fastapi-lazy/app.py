"""FastAPI example with lazy translation loading.

Translations are stored in _gt/<locale>.json and loaded on first request per locale.
Configuration is read from gt.config.json.
Run: uv run uvicorn app:app --port 8001
"""

import json
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from gt_fastapi import initialize_gt, t

app = FastAPI(title="FastAPI Lazy Example")

BASE_DIR = Path(__file__).parent
GT_DIR = BASE_DIR / "_gt"

with open(BASE_DIR / "gt.config.json") as f:
    config = json.load(f)


async def load_translations(locale: str) -> dict[str, str]:
    """Load translations from _gt/<locale>.json."""
    path = GT_DIR / f"{locale}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


manager = initialize_gt(
    app,
    default_locale=config.get("defaultLocale", "en"),
    locales=config.get("locales"),
    load_translations=load_translations,
    eager_loading=False,
)


async def _ensure_translations(request: Request) -> None:
    """Load translations for the current locale if not already cached.

    t() only reads from cache (get_translations_sync), so we must
    explicitly trigger a load for the current locale before t() runs.
    """
    locale = manager.get_locale()
    if manager.requires_translation(locale):
        await manager.get_translations(locale)


# Add dependency to all routes — runs inside route context after middleware
app.router.dependencies = [Depends(_ensure_translations)]


@app.get("/")
def index() -> dict[str, str]:
    return {"message": t("Hello, world!")}


@app.get("/greet")
def greet(name: str = "World") -> dict[str, str]:
    return {"message": t("Hello, {name}!", name=name)}

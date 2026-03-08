"""Flask example with lazy translation loading.

Translations are stored in _gt/<locale>.json and loaded on first request per locale.
Configuration is read from gt.config.json.
Run: uv run python app.py  (serves on port 5051)
"""

import asyncio
import json
from pathlib import Path

from flask import Flask
from gt_flask import initialize_gt, t

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
GT_DIR = BASE_DIR / "_gt"

with open(BASE_DIR / "gt.config.json") as f:
    config = json.load(f)


def load_translations(locale: str) -> dict[str, str]:
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


@app.before_request
def _ensure_translations() -> None:
    """Load translations for the current locale if not already cached.

    Registered after initialize_gt(), so this runs after the locale is set.
    t() only reads from cache (get_translations_sync), so we must
    explicitly trigger a load for the current locale before t() runs.
    """
    locale = manager.get_locale()
    if manager.requires_translation(locale):
        asyncio.run(manager.get_translations(locale))


@app.get("/")
def index() -> dict[str, str]:
    return {"message": t("Hello, world!")}


@app.get("/greet")
def greet() -> dict[str, str]:
    from flask import request

    name = request.args.get("name", "World")
    return {"message": t("Hello, {name}!", name=name)}


if __name__ == "__main__":
    app.run(port=5051)

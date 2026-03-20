"""Flask example with lazy translation loading.

Translations are loaded from _gt/<locale>.json on first request per locale.
Configuration is read from gt.config.json.
Run: uv run python app.py  (serves on port 5051)
"""

import asyncio
import json
from pathlib import Path

from flask import Flask, request
from gt_flask import initialize_gt, t

app = Flask(__name__)

GT_DIR = Path(__file__).parent / "_gt"


def load_translations(locale: str) -> dict[str, str]:
    path = GT_DIR / f"{locale}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


manager = initialize_gt(app, load_translations=load_translations, eager_loading=False)


@app.before_request
def ensure_translations() -> None:
    """Load translations for the request locale before t() runs."""
    locale = manager.get_locale()
    if manager.requires_translation(locale):
        asyncio.run(manager.get_translations(locale))


@app.get("/")
def index() -> dict[str, str]:
    return {"message": t("Hello, world!")}


@app.get("/greet")
def greet() -> dict[str, str]:
    name = request.args.get("name", "World")
    return {"message": t("Hello, {name}!", name=name)}


if __name__ == "__main__":
    app.run(port=5051)

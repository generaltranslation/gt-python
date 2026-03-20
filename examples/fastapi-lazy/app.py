"""FastAPI example with lazy translation loading.

Translations are loaded from _gt/<locale>.json on first request per locale.
Configuration is read from gt.config.json.
Run: uv run uvicorn app:app --port 8001
"""

import json
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from gt_fastapi import initialize_gt, t

app = FastAPI(title="FastAPI Lazy Example")

GT_DIR = Path(__file__).parent / "_gt"


async def load_translations(locale: str) -> dict[str, str]:
    path = GT_DIR / f"{locale}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


manager = initialize_gt(app, load_translations=load_translations, eager_loading=False)


async def ensure_translations(request: Request) -> None:
    """Load translations for the request locale before t() runs."""
    locale = manager.get_locale()
    if manager.requires_translation(locale):
        await manager.get_translations(locale)


app.router.dependencies = [Depends(ensure_translations)]


@app.get("/")
def index() -> dict[str, str]:
    return {"message": t("Hello, world!")}


@app.get("/greet")
def greet(name: str = "World") -> dict[str, str]:
    return {"message": t("Hello, {name}!", name=name)}

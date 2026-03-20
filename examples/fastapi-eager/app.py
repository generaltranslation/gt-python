"""FastAPI example with eager translation loading.

Translations are loaded from _gt/<locale>.json at startup.
Configuration is read from gt.config.json.
Run: uv run uvicorn app:app --port 8000
"""

import json
from pathlib import Path

from fastapi import FastAPI
from gt_fastapi import initialize_gt, t

app = FastAPI(title="FastAPI Eager Example")

GT_DIR = Path(__file__).parent / "_gt"


def load_translations(locale: str) -> dict[str, str]:
    path = GT_DIR / f"{locale}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


initialize_gt(app, load_translations=load_translations)


@app.get("/")
def index() -> dict[str, str]:
    return {"message": t("Hello, world!")}


@app.get("/greet")
def greet(name: str = "World") -> dict[str, str]:
    return {"message": t("Hello, {name}!", name=name)}

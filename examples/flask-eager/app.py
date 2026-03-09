"""Flask example with eager translation loading.

Translations are stored in _gt/<locale>.json and loaded at startup.
Configuration is read automatically from gt.config.json in the CWD.
Run: uv run python app.py  (serves on port 5050)
"""

import json
from pathlib import Path

from flask import Flask
from gt_flask import initialize_gt, t

app = Flask(__name__)

GT_DIR = Path(__file__).parent / "_gt"


def load_translations(locale: str) -> dict[str, str]:
    """Load translations from _gt/<locale>.json."""
    path = GT_DIR / f"{locale}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


initialize_gt(
    app,
    load_translations=load_translations,
    eager_loading=True,
)


@app.get("/")
def index() -> dict[str, str]:
    return {"message": t("Hello, world!")}


@app.get("/greet")
def greet() -> dict[str, str]:
    from flask import request

    name = request.args.get("name", "World")
    return {"message": t("Hello, {name}!", name=name)}


if __name__ == "__main__":
    app.run(port=5050)

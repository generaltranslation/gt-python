"""Flask example with lazy translation loading.

Translations are loaded on the first request for each locale, not at startup;
gt-flask loads them itself before the route runs.
Run: uv run python app.py  (serves on port 5051)
"""

from flask import Flask
from gt_flask import initialize_gt, t

app = Flask(__name__)

TRANSLATIONS: dict[str, dict[str, str]] = {
    "es": {
        "8042e0a3d395c1fb": "Hola, mundo!",
        "9b323e35e1a80c51": "Hola, {name}!",
    },
    "fr": {
        "8042e0a3d395c1fb": "Bonjour, le monde!",
        "9b323e35e1a80c51": "Bonjour, {name}!",
    },
}


def load_translations(locale: str) -> dict[str, str]:
    """Simulate loading translations from a remote source."""
    print(f"[lazy] Loading translations for '{locale}'")
    return TRANSLATIONS.get(locale, {})


manager = initialize_gt(
    app,
    default_locale="en",
    locales=["en", "es", "fr"],
    load_translations=load_translations,
    eager_loading=False,
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
    app.run(port=5051)

"""FastAPI example with eager translation loading.

Translations are loaded at startup for all configured locales.
Run: uv run uvicorn app:app --port 8000
"""

from fastapi import FastAPI
from gt_fastapi import initialize_gt, t

app = FastAPI(title="FastAPI Eager Example")

# Pre-built translation dictionaries keyed by hash.
# hash_message("Hello, world!") -> "8042e0a3d395c1fb"
# hash_message("Hello, {name}!") -> "9b323e35e1a80c51"
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
    """Return translations for a locale from the in-memory dictionary."""
    print(f"[eager] Loading translations for '{locale}'")
    return TRANSLATIONS.get(locale, {})


initialize_gt(
    app,
    default_locale="en",
    locales=["en", "es", "fr"],
    load_translations=load_translations,
    eager_loading=True,
)


@app.get("/")
def index() -> dict[str, str]:
    return {"message": t("Hello, world!")}


@app.get("/greet")
def greet(name: str = "World") -> dict[str, str]:
    return {"message": t("Hello, {name}!", name=name)}

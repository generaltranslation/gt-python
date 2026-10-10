"""FastAPI example with lazy translation loading.

Translations are loaded on the first request for each locale, not at startup;
gt-fastapi loads them itself before the route runs.
Run: uv run uvicorn app:app --port 8001
"""

from fastapi import FastAPI
from gt_fastapi import initialize_gt, t

app = FastAPI(title="FastAPI Lazy Example")

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


async def load_translations(locale: str) -> dict[str, str]:
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
def greet(name: str = "World") -> dict[str, str]:
    return {"message": t("Hello, {name}!", name=name)}

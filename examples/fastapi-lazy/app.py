"""FastAPI example with lazy translation loading.

Translations are loaded on first request per locale, not at startup.
Run: uv run uvicorn app:app --port 8001
"""

from fastapi import Depends, FastAPI, Request
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

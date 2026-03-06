"""Tests for the FastAPI lazy loading example.

Verifies that translations are NOT loaded at startup, are loaded on
first request per locale, and are cached for subsequent requests.
"""

from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from gt_fastapi import initialize_gt, t

TRANSLATIONS = {
    "es": {
        "8042e0a3d395c1fb": "Hola, mundo!",
        "9b323e35e1a80c51": "Hola, {name}!",
    },
    "fr": {
        "8042e0a3d395c1fb": "Bonjour, le monde!",
        "9b323e35e1a80c51": "Bonjour, {name}!",
    },
}


def _create_app():
    load_calls = []

    async def load_translations(locale):
        load_calls.append(locale)
        return TRANSLATIONS.get(locale, {})

    app = FastAPI()
    manager = initialize_gt(
        app,
        default_locale="en",
        locales=["en", "es", "fr"],
        load_translations=load_translations,
        eager_loading=False,
    )

    async def _ensure_translations(request: Request):
        locale = manager.get_locale()
        if manager.requires_translation(locale):
            await manager.get_translations(locale)

    app.router.dependencies = [Depends(_ensure_translations)]

    @app.get("/")
    def index():
        return {"message": t("Hello, world!")}

    @app.get("/greet")
    def greet(name: str = "World"):
        return {"message": t("Hello, {name}!", name=name)}

    return app, load_calls


def test_lazy_does_not_load_at_startup():
    app, load_calls = _create_app()
    with TestClient(app):
        assert len(load_calls) == 0


def test_lazy_loads_on_first_request():
    app, load_calls = _create_app()
    with TestClient(app) as client:
        client.get("/", headers={"Accept-Language": "es"})
        assert "es" in load_calls


def test_lazy_caches_after_first_load():
    app, load_calls = _create_app()
    with TestClient(app) as client:
        client.get("/", headers={"Accept-Language": "es"})
        count_after_first = load_calls.count("es")
        client.get("/", headers={"Accept-Language": "es"})
        assert load_calls.count("es") == count_after_first


def test_english_does_not_trigger_load():
    app, load_calls = _create_app()
    with TestClient(app) as client:
        client.get("/", headers={"Accept-Language": "en"})
        assert len(load_calls) == 0


def test_spanish_translation():
    app, _ = _create_app()
    with TestClient(app) as client:
        resp = client.get("/", headers={"Accept-Language": "es"})
        assert resp.json()["message"] == "Hola, mundo!"


def test_french_translation():
    app, _ = _create_app()
    with TestClient(app) as client:
        resp = client.get("/", headers={"Accept-Language": "fr"})
        assert resp.json()["message"] == "Bonjour, le monde!"


def test_variable_interpolation():
    app, _ = _create_app()
    with TestClient(app) as client:
        resp = client.get("/greet?name=Alice", headers={"Accept-Language": "es"})
        assert resp.json()["message"] == "Hola, Alice!"

        resp = client.get("/greet?name=Bob", headers={"Accept-Language": "fr"})
        assert resp.json()["message"] == "Bonjour, Bob!"

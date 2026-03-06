"""Tests for the FastAPI eager loading example.

Verifies that translations are loaded at startup and all endpoints
return correctly translated content.
"""

from fastapi import FastAPI
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

    def load_translations(locale):
        load_calls.append(locale)
        return TRANSLATIONS.get(locale, {})

    app = FastAPI()
    initialize_gt(
        app,
        default_locale="en",
        locales=["en", "es", "fr"],
        load_translations=load_translations,
        eager_loading=True,
    )

    @app.get("/")
    def index():
        return {"message": t("Hello, world!")}

    @app.get("/greet")
    def greet(name: str = "World"):
        return {"message": t("Hello, {name}!", name=name)}

    return app, load_calls


def test_eager_loads_all_translations_at_startup():
    app, load_calls = _create_app()
    with TestClient(app):
        # All 3 locales loaded during lifespan startup
        assert len(load_calls) == 3
        assert set(load_calls) == {"en", "es", "fr"}


def test_no_additional_loads_on_request():
    app, load_calls = _create_app()
    with TestClient(app) as client:
        initial = len(load_calls)
        client.get("/", headers={"Accept-Language": "es"})
        client.get("/", headers={"Accept-Language": "fr"})
        assert len(load_calls) == initial


def test_english_returns_source():
    app, _ = _create_app()
    with TestClient(app) as client:
        resp = client.get("/", headers={"Accept-Language": "en"})
        assert resp.json()["message"] == "Hello, world!"


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


def test_variable_interpolation_spanish():
    app, _ = _create_app()
    with TestClient(app) as client:
        resp = client.get("/greet?name=Alice", headers={"Accept-Language": "es"})
        assert resp.json()["message"] == "Hola, Alice!"


def test_variable_interpolation_french():
    app, _ = _create_app()
    with TestClient(app) as client:
        resp = client.get("/greet?name=Bob", headers={"Accept-Language": "fr"})
        assert resp.json()["message"] == "Bonjour, Bob!"


def test_greet_default_name():
    app, _ = _create_app()
    with TestClient(app) as client:
        resp = client.get("/greet", headers={"Accept-Language": "en"})
        assert resp.json()["message"] == "Hello, World!"

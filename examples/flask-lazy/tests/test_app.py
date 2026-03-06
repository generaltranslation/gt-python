"""Tests for the Flask lazy loading example.

Verifies that translations are NOT loaded at startup, are loaded on
first request per locale via before_request hook, and are cached.
"""

import asyncio

from flask import Flask

from gt_flask import initialize_gt, t

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

    app = Flask(__name__)
    manager = initialize_gt(
        app,
        default_locale="en",
        locales=["en", "es", "fr"],
        load_translations=load_translations,
        eager_loading=False,
    )

    @app.before_request
    def _ensure_translations():
        locale = manager.get_locale()
        if manager.requires_translation(locale):
            asyncio.run(manager.get_translations(locale))

    @app.get("/")
    def index():
        return {"message": t("Hello, world!")}

    @app.get("/greet")
    def greet():
        from flask import request

        name = request.args.get("name", "World")
        return {"message": t("Hello, {name}!", name=name)}

    return app, load_calls


def test_lazy_does_not_load_at_startup():
    _, load_calls = _create_app()
    assert len(load_calls) == 0


def test_lazy_loads_on_first_request():
    app, load_calls = _create_app()
    with app.test_client() as client:
        client.get("/", headers={"Accept-Language": "es"})
        assert "es" in load_calls


def test_lazy_caches_after_first_load():
    app, load_calls = _create_app()
    with app.test_client() as client:
        client.get("/", headers={"Accept-Language": "es"})
        count_after_first = load_calls.count("es")
        client.get("/", headers={"Accept-Language": "es"})
        assert load_calls.count("es") == count_after_first


def test_english_does_not_trigger_load():
    app, load_calls = _create_app()
    with app.test_client() as client:
        client.get("/", headers={"Accept-Language": "en"})
        assert len(load_calls) == 0


def test_spanish_translation():
    app, _ = _create_app()
    with app.test_client() as client:
        resp = client.get("/", headers={"Accept-Language": "es"})
        assert resp.json["message"] == "Hola, mundo!"


def test_french_translation():
    app, _ = _create_app()
    with app.test_client() as client:
        resp = client.get("/", headers={"Accept-Language": "fr"})
        assert resp.json["message"] == "Bonjour, le monde!"


def test_variable_interpolation():
    app, _ = _create_app()
    with app.test_client() as client:
        resp = client.get("/greet?name=Alice", headers={"Accept-Language": "es"})
        assert resp.json["message"] == "Hola, Alice!"

        resp = client.get("/greet?name=Bob", headers={"Accept-Language": "fr"})
        assert resp.json["message"] == "Bonjour, Bob!"

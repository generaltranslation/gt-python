"""Tests for the Flask eager loading example.

Verifies that translations are loaded at startup (during initialize_gt)
and all endpoints return correctly translated content.
"""

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
    def greet():
        from flask import request

        name = request.args.get("name", "World")
        return {"message": t("Hello, {name}!", name=name)}

    return app, load_calls


def test_eager_loads_all_translations_at_startup():
    _, load_calls = _create_app()
    # Flask eager loading happens synchronously in initialize_gt()
    assert len(load_calls) == 3
    assert set(load_calls) == {"en", "es", "fr"}


def test_no_additional_loads_on_request():
    app, load_calls = _create_app()
    initial = len(load_calls)
    with app.test_client() as client:
        client.get("/", headers={"Accept-Language": "es"})
        client.get("/", headers={"Accept-Language": "fr"})
        assert len(load_calls) == initial


def test_english_returns_source():
    app, _ = _create_app()
    with app.test_client() as client:
        resp = client.get("/", headers={"Accept-Language": "en"})
        assert resp.json["message"] == "Hello, world!"


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


def test_variable_interpolation_spanish():
    app, _ = _create_app()
    with app.test_client() as client:
        resp = client.get("/greet?name=Alice", headers={"Accept-Language": "es"})
        assert resp.json["message"] == "Hola, Alice!"


def test_variable_interpolation_french():
    app, _ = _create_app()
    with app.test_client() as client:
        resp = client.get("/greet?name=Bob", headers={"Accept-Language": "fr"})
        assert resp.json["message"] == "Bonjour, Bob!"


def test_greet_default_name():
    app, _ = _create_app()
    with app.test_client() as client:
        resp = client.get("/greet", headers={"Accept-Language": "en"})
        assert resp.json["message"] == "Hello, World!"

"""Flask integration tests."""

from collections.abc import Generator
from typing import Any

import pytest
from flask import Flask
from gt_flask import initialize_gt, t
from gt_i18n.translation_functions._hash_message import hash_message


@pytest.fixture(autouse=True)
def _reset_singleton() -> Generator[None, None, None]:
    import gt_i18n.i18n_manager._singleton as mod

    old = mod._manager
    yield
    mod._manager = old


def test_flask_t_source_locale() -> None:
    app = Flask(__name__)
    initialize_gt(
        app,
        default_locale="en",
        locales=["en", "es"],
        load_translations=lambda locale: {},
    )

    @app.route("/hello")
    def hello() -> dict[str, Any]:
        return {"message": t("Hello, world!")}

    with app.test_client() as client:
        resp = client.get("/hello", headers={"Accept-Language": "en"})
        assert resp.json is not None
        assert resp.json["message"] == "Hello, world!"


def test_flask_t_with_accept_language() -> None:
    h = hash_message("Hello, world!")

    def loader(locale: str) -> dict[str, str]:
        if locale == "es":
            return {h: "Hola, mundo!"}
        return {}

    app = Flask(__name__)
    initialize_gt(
        app,
        default_locale="en",
        locales=["en", "es"],
        load_translations=loader,
    )

    @app.route("/hello")
    def hello() -> dict[str, Any]:
        return {"message": t("Hello, world!")}

    with app.test_client() as client:
        resp = client.get("/hello", headers={"Accept-Language": "es"})
        assert resp.json is not None
        assert resp.json["message"] == "Hola, mundo!"

        resp = client.get("/hello", headers={"Accept-Language": "en"})
        assert resp.json is not None
        assert resp.json["message"] == "Hello, world!"


def test_flask_custom_get_locale() -> None:
    h = hash_message("Hello!")

    app = Flask(__name__)
    initialize_gt(
        app,
        default_locale="en",
        locales=["en", "fr"],
        load_translations=lambda locale: {h: "Bonjour!"} if locale == "fr" else {},
        get_locale=lambda req: "fr",
    )

    @app.route("/hello")
    def hello() -> dict[str, Any]:
        return {"message": t("Hello!")}

    with app.test_client() as client:
        resp = client.get("/hello")
        assert resp.json is not None
        assert resp.json["message"] == "Bonjour!"


def test_flask_variable_interpolation() -> None:
    h = hash_message("Hello, {name}!")

    app = Flask(__name__)
    initialize_gt(
        app,
        default_locale="en",
        locales=["en", "es"],
        load_translations=lambda locale: {h: "Hola, {name}!"} if locale == "es" else {},
    )

    @app.route("/hello")
    def hello() -> dict[str, Any]:
        return {"message": t("Hello, {name}!", name="Carlos")}

    with app.test_client() as client:
        resp = client.get("/hello", headers={"Accept-Language": "es"})
        assert resp.json is not None
        assert resp.json["message"] == "Hola, Carlos!"

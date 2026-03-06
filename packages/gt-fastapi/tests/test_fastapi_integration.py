"""FastAPI integration tests."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from gt_fastapi import initialize_gt, t
from gt_i18n.translation_functions._hash_message import hash_message


@pytest.fixture(autouse=True)
def _reset_singleton():
    import gt_i18n.i18n_manager._singleton as mod

    old = mod._manager
    yield
    mod._manager = old


def test_fastapi_t_source_locale():
    app = FastAPI()
    initialize_gt(
        app,
        default_locale="en",
        locales=["en", "es"],
        load_translations=lambda locale: {},
    )

    @app.get("/hello")
    def hello():
        return {"message": t("Hello, world!")}

    with TestClient(app) as client:
        resp = client.get("/hello", headers={"Accept-Language": "en"})
        assert resp.json()["message"] == "Hello, world!"


def test_fastapi_t_with_accept_language():
    h = hash_message("Hello, world!")

    def loader(locale):
        if locale == "es":
            return {h: "Hola, mundo!"}
        return {}

    app = FastAPI()
    initialize_gt(
        app,
        default_locale="en",
        locales=["en", "es"],
        load_translations=loader,
    )

    @app.get("/hello")
    def hello():
        return {"message": t("Hello, world!")}

    with TestClient(app) as client:
        resp = client.get("/hello", headers={"Accept-Language": "es"})
        assert resp.json()["message"] == "Hola, mundo!"

        resp = client.get("/hello", headers={"Accept-Language": "en"})
        assert resp.json()["message"] == "Hello, world!"


def test_fastapi_custom_get_locale():
    h = hash_message("Hello!")

    app = FastAPI()
    initialize_gt(
        app,
        default_locale="en",
        locales=["en", "fr"],
        load_translations=lambda locale: {h: "Bonjour!"} if locale == "fr" else {},
        get_locale=lambda req: "fr",
    )

    @app.get("/hello")
    def hello():
        return {"message": t("Hello!")}

    with TestClient(app) as client:
        resp = client.get("/hello")
        assert resp.json()["message"] == "Bonjour!"


def test_fastapi_variable_interpolation():
    h = hash_message("Hello, {name}!")

    app = FastAPI()
    initialize_gt(
        app,
        default_locale="en",
        locales=["en", "es"],
        load_translations=lambda locale: {h: "Hola, {name}!"} if locale == "es" else {},
    )

    @app.get("/hello")
    def hello():
        return {"message": t("Hello, {name}!", name="Carlos")}

    with TestClient(app) as client:
        resp = client.get("/hello", headers={"Accept-Language": "es"})
        assert resp.json()["message"] == "Hola, Carlos!"

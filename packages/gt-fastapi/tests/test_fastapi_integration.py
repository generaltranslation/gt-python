"""FastAPI integration tests."""

import time
from collections.abc import Generator
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from gt_fastapi import initialize_gt, t
from gt_i18n.translation_functions._hash_message import hash_message


@pytest.fixture(autouse=True)
def _reset_singleton() -> Generator[None, None, None]:
    import gt_i18n.i18n_manager._singleton as mod

    old = mod._manager
    yield
    mod._manager = old


def test_fastapi_t_source_locale() -> None:
    app = FastAPI()
    initialize_gt(
        app,
        default_locale="en",
        locales=["en", "es"],
        load_translations=lambda locale: {},
    )

    @app.get("/hello")
    def hello() -> dict[str, Any]:
        return {"message": t("Hello, world!")}

    with TestClient(app) as client:
        resp = client.get("/hello", headers={"Accept-Language": "en"})
        assert resp.json()["message"] == "Hello, world!"


def test_fastapi_t_with_accept_language() -> None:
    h = hash_message("Hello, world!")

    def loader(locale: str) -> dict[str, str]:
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
    def hello() -> dict[str, Any]:
        return {"message": t("Hello, world!")}

    with TestClient(app) as client:
        resp = client.get("/hello", headers={"Accept-Language": "es"})
        assert resp.json()["message"] == "Hola, mundo!"

        resp = client.get("/hello", headers={"Accept-Language": "en"})
        assert resp.json()["message"] == "Hello, world!"


def test_fastapi_custom_get_locale() -> None:
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
    def hello() -> dict[str, Any]:
        return {"message": t("Hello!")}

    with TestClient(app) as client:
        resp = client.get("/hello")
        assert resp.json()["message"] == "Bonjour!"


def test_fastapi_variable_interpolation() -> None:
    h = hash_message("Hello, {name}!")

    app = FastAPI()
    initialize_gt(
        app,
        default_locale="en",
        locales=["en", "es"],
        load_translations=lambda locale: {h: "Hola, {name}!"} if locale == "es" else {},
    )

    @app.get("/hello")
    def hello() -> dict[str, Any]:
        return {"message": t("Hello, {name}!", name="Carlos")}

    with TestClient(app) as client:
        resp = client.get("/hello", headers={"Accept-Language": "es"})
        assert resp.json()["message"] == "Hola, Carlos!"


def test_fastapi_translations_survive_cache_expiry(monkeypatch: pytest.MonkeyPatch) -> None:
    import gt_i18n.i18n_manager._translations_manager as cache

    now = [1_000.0]
    monkeypatch.setattr(cache, "time", SimpleNamespace(monotonic=lambda: now[0]))
    h = hash_message("Hello, world!")
    es_loads = [0]

    def loader(locale: str) -> dict[str, str]:
        if locale != "es":
            return {}
        es_loads[0] += 1
        return {h: "Hola, mundo!"}

    app = FastAPI()
    initialize_gt(app, default_locale="en", locales=["en", "es"], load_translations=loader)

    @app.get("/hello")
    def hello() -> dict[str, Any]:
        return {"message": t("Hello, world!")}

    with TestClient(app) as client:
        first = client.get("/hello", headers={"Accept-Language": "es"})
        now[0] += 120  # two minutes later, past the 60 s cache expiry
        later = client.get("/hello", headers={"Accept-Language": "es"})

        # The reload runs in the background on the app's event loop.
        deadline = time.monotonic() + 5
        while es_loads[0] < 2 and time.monotonic() < deadline:
            time.sleep(0.01)

    assert first.json()["message"] == "Hola, mundo!"
    assert later.json()["message"] == "Hola, mundo!"  # served from the cache while it reloads
    assert es_loads[0] == 2  # es reloaded once, in the background


def test_fastapi_does_not_load_unconfigured_locales() -> None:
    loaded: list[str] = []

    def loader(locale: str) -> dict[str, str]:
        loaded.append(locale)
        return {}

    app = FastAPI()
    initialize_gt(
        app,
        default_locale="en",
        locales=["en", "es"],
        load_translations=loader,
        eager_loading=False,
        get_locale=lambda req: req.query_params.get("lang", "en"),
    )

    @app.get("/hello")
    def hello() -> dict[str, Any]:
        return {"message": t("Hello, world!")}

    with TestClient(app) as client:
        client.get("/hello?lang=es-MX")
        client.get("/hello?lang=es")
    assert loaded == ["es"]


def test_fastapi_lazy_loading_loads_on_first_request() -> None:
    h = hash_message("Hello, world!")
    app = FastAPI()
    initialize_gt(
        app,
        default_locale="en",
        locales=["en", "fr"],
        load_translations=lambda locale: {h: "Bonjour, le monde !"} if locale == "fr" else {},
        eager_loading=False,
    )

    @app.get("/hello")
    def hello() -> dict[str, Any]:
        return {"message": t("Hello, world!")}

    with TestClient(app) as client:
        assert client.get("/hello", headers={"Accept-Language": "fr"}).json()["message"] == "Bonjour, le monde !"

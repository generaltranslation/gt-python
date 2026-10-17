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

        # The reload runs on a background thread.
        deadline = time.monotonic() + 5
        while es_loads[0] < 2 and time.monotonic() < deadline:
            time.sleep(0.01)

    assert first.json()["message"] == "Hola, mundo!"
    assert later.json()["message"] == "Hola, mundo!"  # served from the cache while it reloads
    assert es_loads[0] == 2  # es reloaded once, in the background


@pytest.fixture
def cdn_urls(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Answer the CDN loader with a Spanish greeting and record the URL of each request."""
    import gt_i18n.i18n_manager._remote_loader as remote
    import httpx

    h = hash_message("Hello, world!")
    urls: list[str] = []
    real_client = httpx.AsyncClient

    def handler(request: httpx.Request) -> httpx.Response:
        urls.append(str(request.url))
        return httpx.Response(200, json={h: "Hola, mundo!"})

    monkeypatch.setattr(
        remote.httpx, "AsyncClient", lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw)
    )
    return urls


# gt.config.json settings, initialize_gt() arguments, and the CDN requests for es that follow.
# test_flask_integration.py runs the same cases.
_CDN_CASES = [
    pytest.param(
        {"version_id": "v9", "branch_id": "br_2"},
        {},
        ["https://cdn.gtx.dev/proj/es/v9?branchId=br_2"],
        id="file version and branch",
    ),
    pytest.param(
        {"version_id": "v9", "branch_id": "br_2"},
        {"version_id": "v10"},
        ["https://cdn.gtx.dev/proj/es/v10"],
        id="explicit version drops the file branch",
    ),
    pytest.param({"cache_url": None}, {}, [], id="null cacheUrl turns the CDN off"),
    pytest.param({"cache_url": ""}, {}, [], id="empty cacheUrl turns the CDN off"),
    pytest.param(
        {"cache_url": None},
        {"cache_url": "https://cdn.example.com"},
        ["https://cdn.example.com/proj/es"],
        id="explicit cache_url replaces the file one",
    ),
]


@pytest.mark.parametrize(("file_config", "kwargs", "es_urls"), _CDN_CASES)
def test_fastapi_cdn_settings(
    cdn_urls: list[str], file_config: dict[str, Any], kwargs: dict[str, Any], es_urls: list[str]
) -> None:
    config: Any = {"default_locale": "en", "locales": ["en", "es"], "project_id": "proj", **file_config}
    app = FastAPI()
    initialize_gt(app, load_config=lambda path: config, **kwargs)

    @app.get("/hello")
    def hello() -> dict[str, Any]:
        return {"message": t("Hello, world!")}

    with TestClient(app) as client:
        message = client.get("/hello", headers={"Accept-Language": "es"}).json()["message"]
    assert [url for url in cdn_urls if "/proj/es" in url] == es_urls
    assert message == ("Hola, mundo!" if es_urls else "Hello, world!")


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

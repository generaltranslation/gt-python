"""Flask integration tests."""

import time
from collections.abc import Generator
from types import SimpleNamespace
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


def _hello_app(loader: Any, **kwargs: Any) -> Flask:
    app = Flask(__name__)
    initialize_gt(app, load_translations=loader, **kwargs)

    @app.route("/hello")
    def hello() -> dict[str, Any]:
        return {"message": t("Hello, world!")}

    return app


def test_flask_eager_loads_locales_from_config() -> None:
    h = hash_message("Hello, world!")
    loaded: list[str] = []

    def loader(locale: str) -> dict[str, str]:
        loaded.append(locale)
        return {h: "Hola, mundo!"} if locale == "es" else {}

    app = _hello_app(loader, load_config=lambda path: {"default_locale": "en", "locales": ["en", "es"]})
    assert "es" in loaded  # loaded at startup, before any request

    with app.test_client() as client:
        resp = client.get("/hello", headers={"Accept-Language": "es"})
        assert resp.json is not None
        assert resp.json["message"] == "Hola, mundo!"


def _wait_for(predicate: Any, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() > deadline:
            return False
        time.sleep(0.01)
    return True


def test_flask_translations_survive_cache_expiry(monkeypatch: pytest.MonkeyPatch) -> None:
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

    app = _hello_app(loader, default_locale="en", locales=["en", "es"])

    with app.test_client() as client:
        first = client.get("/hello", headers={"Accept-Language": "es"})
        now[0] += 120  # two minutes later, past the 60 s cache expiry
        later = client.get("/hello", headers={"Accept-Language": "es"})

    assert first.json is not None and later.json is not None
    assert first.json["message"] == "Hola, mundo!"
    assert later.json["message"] == "Hola, mundo!"  # served from the cache while it reloads
    assert _wait_for(lambda: es_loads[0] == 2)  # es reloaded once, in the background


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
# test_fastapi_integration.py runs the same cases.
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
def test_flask_cdn_settings(
    cdn_urls: list[str], file_config: dict[str, Any], kwargs: dict[str, Any], es_urls: list[str]
) -> None:
    config = {"default_locale": "en", "locales": ["en", "es"], "project_id": "proj", **file_config}
    app = _hello_app(None, load_config=lambda path: config, **kwargs)

    with app.test_client() as client:
        resp = client.get("/hello", headers={"Accept-Language": "es"})
    assert [url for url in cdn_urls if "/proj/es" in url] == es_urls
    assert resp.json is not None
    assert resp.json["message"] == ("Hola, mundo!" if es_urls else "Hello, world!")


def test_flask_does_not_load_unconfigured_locales() -> None:
    loaded: list[str] = []

    def loader(locale: str) -> dict[str, str]:
        loaded.append(locale)
        return {}

    app = _hello_app(
        loader,
        default_locale="en",
        locales=["en", "es"],
        eager_loading=False,
        get_locale=lambda req: req.args.get("lang", "en"),
    )
    with app.test_client() as client:
        client.get("/hello?lang=es-MX")
        client.get("/hello?lang=es")
    assert loaded == ["es"]


def test_flask_lazy_loading_loads_on_first_request() -> None:
    h = hash_message("Hello, world!")
    app = _hello_app(
        lambda locale: {h: "Bonjour, le monde !"} if locale == "fr" else {},
        default_locale="en",
        locales=["en", "fr"],
        eager_loading=False,
    )

    with app.test_client() as client:
        resp = client.get("/hello", headers={"Accept-Language": "fr"})
        assert resp.json is not None
        assert resp.json["message"] == "Bonjour, le monde !"

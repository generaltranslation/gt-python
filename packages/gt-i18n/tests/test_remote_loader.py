"""Tests for the CDN translation loader."""

import asyncio
from typing import Any

import httpx
import pytest
from gt_i18n import I18nManager
from gt_i18n.i18n_manager._remote_loader import create_remote_translation_loader


@pytest.fixture
def requests(monkeypatch: pytest.MonkeyPatch) -> list[httpx.Request]:
    """Route the loader's HTTP calls to a fake CDN and record them."""
    import gt_i18n.i18n_manager._remote_loader as mod

    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path.endswith("/missing"):
            return httpx.Response(404)
        if request.url.path.endswith("/empty"):
            return httpx.Response(200, json={})  # what the CDN returns when its backend fails
        return httpx.Response(200, json={"h": "Hola"})

    real_client = httpx.AsyncClient

    def client(**kwargs: Any) -> httpx.AsyncClient:
        return real_client(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(mod.httpx, "AsyncClient", client)
    return seen


def test_defaults_to_the_gt_cdn(requests: list[httpx.Request]) -> None:
    loader = create_remote_translation_loader("proj")
    assert asyncio.run(loader("es")) == {"h": "Hola"}  # type: ignore[arg-type]
    assert str(requests[0].url) == "https://cdn.gtx.dev/proj/es"


def test_version_id_pins_the_url(requests: list[httpx.Request]) -> None:
    loader = create_remote_translation_loader("proj", "https://cdn.example", version_id="v42")
    asyncio.run(loader("es"))  # type: ignore[arg-type]
    assert str(requests[0].url) == "https://cdn.example/proj/es/v42"


def test_failed_request_raises(requests: list[httpx.Request]) -> None:
    loader = create_remote_translation_loader("proj")
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(loader("missing"))  # type: ignore[arg-type]


def test_manager_without_cache_url_uses_the_gt_cdn(requests: list[httpx.Request]) -> None:
    manager = I18nManager(default_locale="en", locales=["es"], project_id="proj", version_id="v7")
    assert asyncio.run(manager.get_translations("es")) == {"h": "Hola"}
    assert str(requests[0].url) == "https://cdn.gtx.dev/proj/es/v7"


def test_empty_response_raises(requests: list[httpx.Request]) -> None:
    loader = create_remote_translation_loader("proj")
    with pytest.raises(ValueError):
        asyncio.run(loader("empty"))  # type: ignore[arg-type]


def test_branch_id_is_sent_as_a_query(requests: list[httpx.Request]) -> None:
    loader = create_remote_translation_loader("proj", version_id="v42", branch_id="br_7")
    asyncio.run(loader("es"))  # type: ignore[arg-type]
    assert str(requests[0].url) == "https://cdn.gtx.dev/proj/es/v42?branchId=br_7"


def test_empty_cache_url_turns_cdn_loading_off(requests: list[httpx.Request]) -> None:
    manager = I18nManager(default_locale="en", locales=["es"], project_id="proj", cache_url="")
    assert asyncio.run(manager.get_translations("es")) == {}
    assert requests == []

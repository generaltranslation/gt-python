"""Tests for TranslationsManager."""

import asyncio
import threading
from collections.abc import Callable
from types import SimpleNamespace

import pytest
from gt_i18n.i18n_manager._translations_manager import TranslationsLoader, TranslationsManager


@pytest.fixture
def sample_translations() -> dict[str, str]:
    return {"greeting_hash": "Hola, mundo!"}


def test_custom_loader(sample_translations: dict[str, str]) -> None:
    def loader(locale: str) -> dict[str, str]:
        if locale == "es":
            return sample_translations
        return {}

    mgr = TranslationsManager(loader)
    result = asyncio.run(mgr.get_translations("es"))
    assert result == sample_translations


def test_cache_hit(sample_translations: dict[str, str]) -> None:
    call_count = [0]

    def loader(locale: str) -> dict[str, str]:
        call_count[0] += 1
        return sample_translations

    mgr = TranslationsManager(loader, cache_expiry_time=60_000)
    asyncio.run(mgr.get_translations("es"))
    asyncio.run(mgr.get_translations("es"))
    assert call_count[0] == 1


def test_sync_returns_cached(sample_translations: dict[str, str]) -> None:
    def loader(locale: str) -> dict[str, str]:
        return sample_translations

    mgr = TranslationsManager(loader)
    # Before loading, sync returns empty
    assert mgr.get_translations_sync("es") == {}
    # After loading
    asyncio.run(mgr.get_translations("es"))
    assert mgr.get_translations_sync("es") == sample_translations


def test_load_all() -> None:
    loaded = []

    def loader(locale: str) -> dict[str, str]:
        loaded.append(locale)
        return {f"{locale}_hash": f"{locale}_value"}

    mgr = TranslationsManager(loader)
    asyncio.run(mgr.load_all(["en", "es", "fr"]))
    assert set(loaded) == {"en", "es", "fr"}
    assert mgr.get_translations_sync("es") == {"es_hash": "es_value"}


def test_loader_error_returns_empty() -> None:
    def loader(locale: str) -> dict[str, str]:
        raise RuntimeError("fail")

    mgr = TranslationsManager(loader)
    result = asyncio.run(mgr.get_translations("es"))
    assert result == {}


def test_async_loader() -> None:
    async def loader(locale: str) -> dict[str, str]:
        return {"async_hash": "async_value"}

    mgr = TranslationsManager(loader)
    result = asyncio.run(mgr.get_translations("es"))
    assert result == {"async_hash": "async_value"}


class _Clock:
    """Stands in for ``time.monotonic`` in the cache module only, so asyncio's own clock keeps running."""

    def __init__(self) -> None:
        self.now = 1_000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> _Clock:
    import gt_i18n.i18n_manager._translations_manager as mod

    c = _Clock()
    monkeypatch.setattr(mod, "time", SimpleNamespace(monotonic=c))
    return c


def _counting(values: list[dict[str, str]]) -> tuple[Callable[[str], dict[str, str]], list[int]]:
    """A loader that returns *values* in order (repeating the last) and counts its calls."""
    calls = [0]

    def loader(locale: str) -> dict[str, str]:
        calls[0] += 1
        return values[min(calls[0], len(values)) - 1]

    return loader, calls


def _settle(mgr: TranslationsManager, locale: str) -> None:
    """Wait for a background reload of *locale* to finish."""
    with mgr._lock_for(locale):
        pass


def test_sync_serves_last_loaded_after_expiry(clock: _Clock, sample_translations: dict[str, str]) -> None:
    mgr = TranslationsManager(lambda locale: sample_translations, cache_expiry_time=60_000)
    asyncio.run(mgr.get_translations("es"))
    clock.now += 61
    assert mgr.get_translations_sync("es") == sample_translations


def test_expired_entry_is_served_while_it_reloads(clock: _Clock) -> None:
    loader, calls = _counting([{"h": "v1"}, {"h": "v2"}])
    mgr = TranslationsManager(loader, cache_expiry_time=60_000)

    async def scenario() -> tuple[dict[str, str], dict[str, str]]:
        await mgr.get_translations("es")
        clock.now += 61
        served = await mgr.get_translations("es")  # the stale copy, at once
        _settle(mgr, "es")
        return served, mgr.get_translations_sync("es")

    assert asyncio.run(scenario()) == ({"h": "v1"}, {"h": "v2"})
    assert calls[0] == 2


def test_one_off_event_loops_still_refresh_after_expiry(clock: _Clock) -> None:
    loader, calls = _counting([{"h": "v1"}, {"h": "v2"}])
    mgr = TranslationsManager(loader, cache_expiry_time=60_000)
    assert asyncio.run(mgr.get_translations("es")) == {"h": "v1"}
    clock.now += 61
    assert asyncio.run(mgr.get_translations("es")) == {"h": "v1"}  # this loop ends right away
    _settle(mgr, "es")
    assert mgr.get_translations_sync("es") == {"h": "v2"}
    assert calls[0] == 2


def test_async_loader_reloads_on_the_callers_event_loop(clock: _Clock) -> None:
    loops: list[asyncio.AbstractEventLoop] = []

    async def loader(locale: str) -> dict[str, str]:
        loops.append(asyncio.get_running_loop())  # a client bound to the app's loop works only there
        return {"h": f"v{len(loops)}"}

    mgr = TranslationsManager(loader, cache_expiry_time=60_000)

    async def scenario() -> asyncio.AbstractEventLoop:
        await mgr.get_translations("es")
        clock.now += 61
        assert await mgr.get_translations("es") == {"h": "v1"}  # served at once while it reloads
        await mgr.load_all(["es"])  # waits for that reload instead of starting another
        return asyncio.get_running_loop()

    app_loop = asyncio.run(scenario())
    assert loops == [app_loop, app_loop]
    assert mgr.get_translations_sync("es") == {"h": "v2"}


def test_async_reload_finishes_after_a_one_off_event_loop_closes(clock: _Clock) -> None:
    finished = [0]

    async def loader(locale: str) -> dict[str, str]:
        await asyncio.sleep(0.01)  # still running when the caller's loop closes
        finished[0] += 1
        return {"h": f"v{finished[0]}"}

    mgr = TranslationsManager(loader, cache_expiry_time=60_000)
    assert asyncio.run(mgr.get_translations("es")) == {"h": "v1"}
    clock.now += 61
    assert asyncio.run(mgr.get_translations("es")) == {"h": "v1"}
    _settle(mgr, "es")  # the reload moved to a thread when that loop closed
    assert mgr.get_translations_sync("es") == {"h": "v2"}


def _gated(*, is_async: bool) -> tuple[TranslationsLoader, threading.Event, list[int]]:
    """A loader whose second call, the first reload, waits for the returned gate; it counts its calls."""
    gate = threading.Event()
    calls = [0]

    def load(locale: str) -> dict[str, str]:
        calls[0] += 1
        n = calls[0]
        if n == 2:
            gate.wait(5)
        return {"h": f"v{n}"}

    async def load_async(locale: str) -> dict[str, str]:
        return load(locale)

    return (load_async if is_async else load), gate, calls


def test_load_all_shares_the_running_reload(clock: _Clock) -> None:
    loader, gate, calls = _gated(is_async=False)
    mgr = TranslationsManager(loader, cache_expiry_time=60_000)

    async def scenario() -> None:
        await mgr.get_translations("es")
        clock.now += 61
        await mgr.get_translations("es")  # starts the reload
        load_all = asyncio.ensure_future(mgr.load_all(["es"]))
        await asyncio.sleep(0.05)
        gate.set()
        await load_all

    asyncio.run(scenario())
    assert calls[0] == 2  # one reload, which load_all waited for
    assert mgr.get_translations_sync("es") == {"h": "v2"}


@pytest.mark.parametrize("is_async", [False, True], ids=["sync loader", "async loader"])
def test_load_all_blocking_shares_the_running_reload(clock: _Clock, is_async: bool) -> None:
    loader, gate, calls = _gated(is_async=is_async)
    mgr = TranslationsManager(loader, cache_expiry_time=60_000)
    mgr.get_translations_blocking("es")
    clock.now += 61
    mgr.get_translations_blocking("es")  # starts the reload
    threading.Timer(0.05, gate.set).start()
    mgr.load_all_blocking(["es"])
    assert calls[0] == 2  # one reload, which load_all_blocking waited for
    assert mgr.get_translations_sync("es") == {"h": "v2"}


def test_async_read_starts_no_reload_while_a_thread_reloads(clock: _Clock) -> None:
    loader, gate, calls = _gated(is_async=True)
    mgr = TranslationsManager(loader, cache_expiry_time=60_000)
    mgr.get_translations_blocking("es")
    clock.now += 61
    mgr.get_translations_blocking("es")  # reloads on a thread
    assert asyncio.run(mgr.get_translations("es")) == {"h": "v1"}
    gate.set()
    _settle(mgr, "es")
    assert calls[0] == 2
    assert mgr.get_translations_sync("es") == {"h": "v2"}


def test_failed_reload_keeps_previous_translations(clock: _Clock, sample_translations: dict[str, str]) -> None:
    calls = [0]

    def loader(locale: str) -> dict[str, str]:
        calls[0] += 1
        if calls[0] > 1:
            raise RuntimeError("CDN unavailable")
        return sample_translations

    mgr = TranslationsManager(loader, cache_expiry_time=60_000)

    async def scenario() -> None:
        await mgr.get_translations("es")
        clock.now += 61
        await mgr.get_translations("es")
        _settle(mgr, "es")
        # The failed attempt counts as a load, so nothing retries until the next expiry.
        await mgr.get_translations("es")

    asyncio.run(scenario())
    assert mgr.get_translations_sync("es") == sample_translations
    assert calls[0] == 2


def test_concurrent_first_loads_share_one_load() -> None:
    calls = [0]

    async def loader(locale: str) -> dict[str, str]:
        calls[0] += 1
        await asyncio.sleep(0.01)
        return {"h": locale}

    mgr = TranslationsManager(loader)

    async def scenario() -> list[dict[str, str]]:
        return list(await asyncio.gather(*(mgr.get_translations("es") for _ in range(5))))

    assert asyncio.run(scenario()) == [{"h": "es"}] * 5
    assert calls[0] == 1


def test_cancelled_caller_does_not_cancel_the_load() -> None:
    async def loader(locale: str) -> dict[str, str]:
        await asyncio.sleep(0.05)
        return {"h": locale}

    mgr = TranslationsManager(loader)

    async def scenario() -> dict[str, str]:
        first = asyncio.ensure_future(mgr.get_translations("es"))
        second = asyncio.ensure_future(mgr.get_translations("es"))
        await asyncio.sleep(0.01)
        first.cancel()
        return await second

    assert asyncio.run(scenario()) == {"h": "es"}
    assert mgr.get_translations_sync("es") == {"h": "es"}


def test_separate_event_loops_do_not_share_loads() -> None:
    async def loader(locale: str) -> dict[str, str]:
        await asyncio.sleep(0.05)
        return {"h": locale}

    mgr = TranslationsManager(loader)
    results: list[dict[str, str]] = []
    errors: list[BaseException] = []

    def worker() -> None:
        try:
            results.append(asyncio.run(mgr.get_translations("es")))
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    assert errors == []
    assert results == [{"h": "es"}, {"h": "es"}]


def test_sync_loader_runs_off_the_event_loop() -> None:
    loader_threads: list[int] = []

    def loader(locale: str) -> dict[str, str]:
        loader_threads.append(threading.get_ident())
        return {"h": locale}

    mgr = TranslationsManager(loader)

    async def scenario() -> int:
        await mgr.get_translations("es")
        return threading.get_ident()

    loop_thread = asyncio.run(scenario())
    assert loader_threads and loader_threads[0] != loop_thread


def test_blocking_first_load_waits_and_loads_once() -> None:
    gate = threading.Event()
    calls = [0]

    def loader(locale: str) -> dict[str, str]:
        calls[0] += 1
        gate.wait(5)
        return {"h": locale}

    mgr = TranslationsManager(loader)
    results: list[dict[str, str]] = []
    threads = [threading.Thread(target=lambda: results.append(mgr.get_translations_blocking("es"))) for _ in range(4)]
    for th in threads:
        th.start()
    gate.set()
    for th in threads:
        th.join()
    assert results == [{"h": "es"}] * 4
    assert calls[0] == 1


def test_blocking_expired_entry_is_served_without_waiting(clock: _Clock) -> None:
    gate = threading.Event()
    calls = [0]

    def loader(locale: str) -> dict[str, str]:
        calls[0] += 1
        if calls[0] > 1:
            gate.wait(5)  # a slow reload
        return {"h": f"v{calls[0]}"}

    mgr = TranslationsManager(loader, cache_expiry_time=60_000)
    assert mgr.get_translations_blocking("es") == {"h": "v1"}
    clock.now += 61
    assert mgr.get_translations_blocking("es") == {"h": "v1"}  # returns while the reload is blocked
    assert mgr.get_translations_blocking("es") == {"h": "v1"}  # and does not start a second reload
    gate.set()
    _settle(mgr, "es")
    assert mgr.get_translations_sync("es") == {"h": "v2"}
    assert calls[0] == 2


def test_blocking_failed_reload_keeps_previous_translations(clock: _Clock) -> None:
    calls = [0]

    def loader(locale: str) -> dict[str, str]:
        calls[0] += 1
        if calls[0] > 1:
            raise RuntimeError("CDN unavailable")
        return {"h": "v1"}

    mgr = TranslationsManager(loader, cache_expiry_time=60_000)
    mgr.get_translations_blocking("es")
    clock.now += 61
    mgr.get_translations_blocking("es")
    _settle(mgr, "es")
    assert mgr.get_translations_sync("es") == {"h": "v1"}


def test_blocking_load_runs_async_loader() -> None:
    async def loader(locale: str) -> dict[str, str]:
        return {"async_hash": locale}

    mgr = TranslationsManager(loader)
    assert mgr.get_translations_blocking("fr") == {"async_hash": "fr"}


def test_blocking_load_inside_running_loop() -> None:
    async def loader(locale: str) -> dict[str, str]:
        return {"h": locale}

    mgr = TranslationsManager(loader)

    async def caller() -> dict[str, str]:
        return mgr.get_translations_blocking("de")

    assert asyncio.run(caller()) == {"h": "de"}


def test_load_all_blocking_inside_running_loop() -> None:
    loader, calls = _counting([{"h": "x"}])
    mgr = TranslationsManager(loader)

    async def caller() -> None:
        mgr.load_all_blocking(["es", "fr"])

    asyncio.run(caller())
    assert calls[0] == 2
    assert mgr.get_translations_sync("fr") == {"h": "x"}

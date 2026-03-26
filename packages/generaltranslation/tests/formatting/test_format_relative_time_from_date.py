"""Tests for select_relative_time_unit and format_relative_time_from_date."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from generaltranslation.formatting import (
    format_relative_time_from_date,
    select_relative_time_unit,
)

FROZEN_NOW = datetime(2026, 3, 26, 12, 0, 0, tzinfo=timezone.utc)


def _make_date(delta: timedelta) -> datetime:
    return FROZEN_NOW + delta


@pytest.fixture(autouse=True)
def _freeze_now():
    """Patch datetime.now in the module under test to return FROZEN_NOW."""
    target = "generaltranslation.formatting._format_relative_time.datetime"
    with patch(target, wraps=datetime) as mock_dt:
        mock_dt.now.return_value = FROZEN_NOW
        yield


# --- select_relative_time_unit ---

@pytest.mark.parametrize(
    "delta, expected_unit, expected_value",
    [
        (timedelta(seconds=-30), "second", -30),
        (timedelta(seconds=45), "second", 45),
        (timedelta(minutes=-5), "minute", -5),
        (timedelta(minutes=30), "minute", 30),
        (timedelta(hours=-3), "hour", -3),
        (timedelta(hours=10), "hour", 10),
        (timedelta(days=-3), "day", -3),
        (timedelta(days=5), "day", 5),
        (timedelta(days=-14), "week", -2),
        (timedelta(days=21), "week", 3),
        (timedelta(days=-90), "month", -3),
        (timedelta(days=180), "month", 6),
        (timedelta(days=-400), "year", -1),
        (timedelta(days=730), "year", 2),
    ],
)
def test_select_relative_time_unit(delta, expected_unit, expected_value):
    value, unit = select_relative_time_unit(_make_date(delta))
    assert unit == expected_unit
    assert value == expected_value


def test_naive_datetime_treated_as_utc():
    naive_date = FROZEN_NOW.replace(tzinfo=None) - timedelta(hours=2)
    value, unit = select_relative_time_unit(naive_date)
    assert unit == "hour"
    assert value == -2


# --- format_relative_time_from_date ---

def test_format_english_past():
    result = format_relative_time_from_date(
        _make_date(timedelta(hours=-3)), locales="en"
    )
    assert "3 hours ago" in result


def test_format_english_future():
    result = format_relative_time_from_date(
        _make_date(timedelta(days=2)), locales="en"
    )
    assert "2 days" in result


def test_format_spanish():
    result = format_relative_time_from_date(
        _make_date(timedelta(minutes=-10)), locales="es"
    )
    assert "10" in result


def test_format_short_style():
    result = format_relative_time_from_date(
        _make_date(timedelta(days=-3)),
        locales="en",
        options={"style": "short"},
    )
    assert result  # doesn't crash

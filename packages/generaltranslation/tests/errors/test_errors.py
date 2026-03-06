"""Tests for the errors module."""

import pytest
from generaltranslation.errors import (
    GT_ERROR_PREFIX,
    INVALID_AUTH_ERROR,
    ApiError,
    api_error_message,
    create_invalid_cutoff_style_error,
    invalid_locale_error,
    invalid_locales_error,
    no_api_key_error,
    no_project_id_error,
    no_source_locale_error,
    no_target_locale_error,
    translation_request_failed_error,
    translation_timeout_error,
)


class TestApiError:
    """Tests for the ApiError exception class."""

    def test_is_exception(self) -> None:
        err = ApiError("something went wrong", code=500, message="Internal Server Error")
        assert isinstance(err, Exception)

    def test_attributes(self) -> None:
        err = ApiError("something went wrong", code=404, message="Not Found")
        assert err.code == 404
        assert err.message == "Not Found"

    def test_str_matches_error_arg(self) -> None:
        err = ApiError("custom error text", code=400, message="Bad Request")
        assert str(err) == "custom error text"

    def test_can_be_raised_and_caught(self) -> None:
        with pytest.raises(ApiError) as exc_info:
            raise ApiError("boom", code=503, message="Service Unavailable")
        assert exc_info.value.code == 503
        assert exc_info.value.message == "Service Unavailable"


class TestErrorMessages:
    """Tests for all error message helpers and constants."""

    def test_gt_error_prefix(self) -> None:
        assert GT_ERROR_PREFIX == "GT Error:"

    def test_invalid_auth_error(self) -> None:
        assert INVALID_AUTH_ERROR == "GT Error: Invalid authentication."

    def test_translation_timeout_error(self) -> None:
        result = translation_timeout_error(5000)
        assert result == "GT Error: Translation request timed out after 5000ms."

    def test_translation_request_failed_error(self) -> None:
        result = translation_request_failed_error("Network failure")
        assert result == "GT Error: Translation request failed. Error: Network failure"

    def test_api_error_message(self) -> None:
        result = api_error_message(500, "Internal Server Error", "unexpected crash")
        assert (
            result == "GT Error: API returned error status."
            " Status: 500, Status Text: Internal Server Error, Error: unexpected crash"
        )

    def test_no_target_locale_error(self) -> None:
        result = no_target_locale_error("translate")
        assert (
            result == "GT Error: Cannot call `translate` without a specified locale."
            " Either pass a locale to the `translate` function or specify a targetLocale in the GT constructor."
        )

    def test_no_source_locale_error(self) -> None:
        result = no_source_locale_error("translate")
        assert (
            result == "GT Error: Cannot call `translate` without a specified locale."
            " Either pass a locale to the `translate` function or specify a sourceLocale in the GT constructor."
        )

    def test_no_project_id_error(self) -> None:
        result = no_project_id_error("translate")
        assert (
            result == "GT Error: Cannot call `translate` without a specified project ID."
            " Either pass a project ID to the `translate` function or specify a projectId in the GT constructor."
        )

    def test_no_api_key_error(self) -> None:
        result = no_api_key_error("translate")
        assert (
            result == "GT Error: Cannot call `translate` without a specified API key."
            " Either pass an API key to the `translate` function or specify an apiKey in the GT constructor."
        )

    def test_invalid_locale_error(self) -> None:
        result = invalid_locale_error("xx-YY")
        assert result == "GT Error: Invalid locale: xx-YY."

    def test_invalid_locales_error(self) -> None:
        result = invalid_locales_error(["xx", "yy", "zz"])
        assert result == "GT Error: Invalid locales: xx, yy, zz."

    def test_invalid_locales_error_single(self) -> None:
        result = invalid_locales_error(["xx"])
        assert result == "GT Error: Invalid locales: xx."

    def test_create_invalid_cutoff_style_error(self) -> None:
        result = create_invalid_cutoff_style_error("bad-style")
        assert result == "generaltranslation Formatting Error: Invalid cutoff style: bad-style."

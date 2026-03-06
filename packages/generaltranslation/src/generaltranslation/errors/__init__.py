"""Error types for General Translation."""

from generaltranslation.errors._api_error import ApiError
from generaltranslation.errors._messages import (
    GT_ERROR_PREFIX,
    INVALID_AUTH_ERROR,
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

__all__ = [
    "ApiError",
    "GT_ERROR_PREFIX",
    "INVALID_AUTH_ERROR",
    "api_error_message",
    "create_invalid_cutoff_style_error",
    "invalid_locale_error",
    "invalid_locales_error",
    "no_api_key_error",
    "no_project_id_error",
    "no_source_locale_error",
    "no_target_locale_error",
    "translation_request_failed_error",
    "translation_timeout_error",
]

GT_ERROR_PREFIX = "GT Error:"


def translation_timeout_error(timeout: int) -> str:
    return f"{GT_ERROR_PREFIX} Translation request timed out after {timeout}ms."


def translation_request_failed_error(error: str) -> str:
    return f"{GT_ERROR_PREFIX} Translation request failed. Error: {error}"


def api_error_message(status: int, status_text: str, error: str) -> str:
    return f"{GT_ERROR_PREFIX} API returned error status. Status: {status}, Status Text: {status_text}, Error: {error}"


INVALID_AUTH_ERROR = f"{GT_ERROR_PREFIX} Invalid authentication."


def no_target_locale_error(fn_name: str) -> str:
    return (
        f"{GT_ERROR_PREFIX} Cannot call `{fn_name}` without a specified locale."
        f" Either pass a locale to the `{fn_name}` function or specify a targetLocale in the GT constructor."
    )


def no_source_locale_error(fn_name: str) -> str:
    return (
        f"{GT_ERROR_PREFIX} Cannot call `{fn_name}` without a specified locale."
        f" Either pass a locale to the `{fn_name}` function or specify a sourceLocale in the GT constructor."
    )


def no_project_id_error(fn_name: str) -> str:
    return (
        f"{GT_ERROR_PREFIX} Cannot call `{fn_name}` without a specified project ID."
        f" Either pass a project ID to the `{fn_name}` function or specify a projectId in the GT constructor."
    )


def no_api_key_error(fn_name: str) -> str:
    return (
        f"{GT_ERROR_PREFIX} Cannot call `{fn_name}` without a specified API key."
        f" Either pass an API key to the `{fn_name}` function or specify an apiKey in the GT constructor."
    )


def invalid_locale_error(locale: str) -> str:
    return f"{GT_ERROR_PREFIX} Invalid locale: {locale}."


def invalid_locales_error(locales: list[str]) -> str:
    return f"{GT_ERROR_PREFIX} Invalid locales: {', '.join(locales)}."


def create_invalid_cutoff_style_error(style: str) -> str:
    return f"generaltranslation Formatting Error: Invalid cutoff style: {style}."

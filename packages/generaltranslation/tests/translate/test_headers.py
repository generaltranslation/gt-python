from generaltranslation._settings import API_VERSION
from generaltranslation.translate._headers import generate_request_headers


def test_basic_headers() -> None:
    config = {"project_id": "proj-123", "api_key": "my-key"}
    headers = generate_request_headers(config)
    assert headers["Content-Type"] == "application/json"
    assert headers["x-gt-project-id"] == "proj-123"
    assert headers["x-gt-api-key"] == "my-key"
    assert headers["gt-api-version"] == API_VERSION


def test_exclude_content_type() -> None:
    config = {"project_id": "proj-123"}
    headers = generate_request_headers(config, exclude_content_type=True)
    assert "Content-Type" not in headers


def test_internal_api_key() -> None:
    config = {"project_id": "proj-123", "api_key": "gtx-internal-abc"}
    headers = generate_request_headers(config)
    assert "x-gt-internal-api-key" in headers
    assert headers["x-gt-internal-api-key"] == "gtx-internal-abc"
    assert "x-gt-api-key" not in headers


def test_no_api_key() -> None:
    config = {"project_id": "proj-123"}
    headers = generate_request_headers(config)
    assert "x-gt-api-key" not in headers
    assert "x-gt-internal-api-key" not in headers

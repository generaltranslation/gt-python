import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from generaltranslation.translate._request import api_request
from generaltranslation.errors import ApiError

@pytest.fixture
def config():
    return {"project_id": "proj-123", "api_key": "test-key", "base_url": "https://test.api.com"}

@pytest.mark.asyncio
async def test_successful_post(config):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "ok"}

    with patch("generaltranslation.translate._request.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await api_request(config, "/v2/test", body={"key": "value"})
        assert result == {"result": "ok"}

@pytest.mark.asyncio
async def test_successful_get(config):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [1, 2, 3]}

    with patch("generaltranslation.translate._request.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await api_request(config, "/v2/test", method="GET")
        assert result == {"data": [1, 2, 3]}

@pytest.mark.asyncio
async def test_4xx_raises_api_error(config):
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.reason_phrase = "Unauthorized"
    mock_response.text = json.dumps({"error": "Invalid API key"})

    with patch("generaltranslation.translate._request.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises(ApiError) as exc_info:
            await api_request(config, "/v2/test", body={})
        assert exc_info.value.code == 401

@pytest.mark.asyncio
async def test_timeout_raises_error(config):
    with patch("generaltranslation.translate._request.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.TimeoutException("timed out")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises(Exception, match="timed out"):
            await api_request(config, "/v2/test", body={}, retry_policy="none")

@pytest.mark.asyncio
async def test_no_retry_on_none_policy(config):
    call_count = 0
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.reason_phrase = "Internal Server Error"
    mock_response.text = "Server error"

    with patch("generaltranslation.translate._request.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        async def counting_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return mock_response
        mock_client.post = counting_post
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises(ApiError):
            await api_request(config, "/v2/test", body={}, retry_policy="none")
        assert call_count == 1


@pytest.mark.asyncio
async def test_client_reused_across_retries(config):
    """AsyncClient should be instantiated once even when retries occur."""
    # First call returns 500 (triggers retry), second returns 200
    mock_response_500 = MagicMock()
    mock_response_500.status_code = 500
    mock_response_500.reason_phrase = "Internal Server Error"
    mock_response_500.text = "error"

    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"ok": True}

    with patch("generaltranslation.translate._request.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=[mock_response_500, mock_response_200])
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with patch("generaltranslation.translate._request.asyncio.sleep", new_callable=AsyncMock):
            result = await api_request(config, "/v2/test", body={})

        assert result == {"ok": True}
        assert mock_client_cls.call_count == 1, (
            f"AsyncClient should be created once, was created {mock_client_cls.call_count} times"
        )

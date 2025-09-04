"""Tests for App Store Connect API client."""

import json
from unittest.mock import Mock, patch

import httpx
import pytest

from koubou.appstore.auth import AppStoreAuth
from koubou.appstore.client import AppStoreAPIError, AppStoreClient


@pytest.fixture
def mock_auth():
    """Create mock authentication object."""
    auth = Mock(spec=AppStoreAuth)
    auth.get_auth_headers.return_value = {
        "Authorization": "Bearer test_token",
        "Content-Type": "application/json",
    }
    return auth


@pytest.fixture
def client(mock_auth):
    """Create client instance with mock auth."""
    return AppStoreClient(mock_auth, timeout=10.0)


class TestAppStoreClient:
    """Test AppStoreClient class."""

    def test_init(self, mock_auth):
        """Test client initialization."""
        client = AppStoreClient(mock_auth, timeout=15.0)

        assert client.auth == mock_auth
        assert client.timeout == 15.0
        assert client.base_url == "https://api.appstoreconnect.apple.com/v1"
        assert isinstance(client.client, httpx.Client)

    def test_context_manager(self, mock_auth):
        """Test client as context manager."""
        with AppStoreClient(mock_auth) as client:
            assert isinstance(client, AppStoreClient)
        # Client should be closed after context exit

    @patch("httpx.Client.request")
    def test_make_request_success_json(self, mock_request, client):
        """Test successful request with JSON response."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"data": {"id": "123", "type": "apps"}}
        mock_request.return_value = mock_response

        result = client._make_request("GET", "apps/123")

        assert result == {"data": {"id": "123", "type": "apps"}}

        # Verify request was made correctly
        mock_request.assert_called_once_with(
            method="GET",
            url="https://api.appstoreconnect.apple.com/v1/apps/123",
            json=None,
            params=None,
            files=None,
            headers={
                "Authorization": "Bearer test_token",
                "Content-Type": "application/json",
            },
        )

    @patch("httpx.Client.request")
    def test_make_request_success_text(self, mock_request, client):
        """Test successful request with text response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.text = "Success"
        mock_request.return_value = mock_response

        result = client._make_request("GET", "apps/123")

        assert result == {"status": "success", "data": "Success"}

    @patch("httpx.Client.request")
    def test_make_request_with_data(self, mock_request, client):
        """Test request with JSON data."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"data": {"id": "456"}}
        mock_request.return_value = mock_response

        request_data = {"data": {"type": "apps", "attributes": {"name": "Test App"}}}
        result = client._make_request("POST", "apps", data=request_data)

        assert result == {"data": {"id": "456"}}

        # Verify JSON data was passed
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args.kwargs
        assert call_kwargs["json"] == request_data

    @patch("httpx.Client.request")
    def test_make_request_with_files(self, mock_request, client):
        """Test request with file upload."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"status": "uploaded"}
        mock_request.return_value = mock_response

        files = {"file": ("test.png", b"image_data", "image/png")}
        result = client._make_request("PUT", "upload", files=files)

        assert result == {"status": "uploaded"}

        # Verify Content-Type header was removed for multipart uploads
        call_kwargs = mock_request.call_args.kwargs
        assert "Content-Type" not in call_kwargs["headers"]
        assert call_kwargs["files"] == files

    @patch("httpx.Client.request")
    def test_make_request_api_error(self, mock_request, client):
        """Test request with API error response."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {"content-type": "application/json"}
        mock_response.content = (
            b'{"errors": [{"code": "INVALID_REQUEST", '
            b'"detail": "The request is invalid"}]}'
        )
        mock_response.json.return_value = {
            "errors": [{"code": "INVALID_REQUEST", "detail": "The request is invalid"}]
        }
        mock_request.return_value = mock_response

        with pytest.raises(AppStoreAPIError) as exc_info:
            client._make_request("GET", "apps/invalid")

        error = exc_info.value
        assert error.status_code == 400
        assert "INVALID_REQUEST: The request is invalid" in str(error)
        assert error.response_data["errors"][0]["code"] == "INVALID_REQUEST"

    @patch("httpx.Client.request")
    def test_make_request_http_error_no_json(self, mock_request, client):
        """Test request with HTTP error and no JSON response."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.content = b"Internal Server Error"
        mock_response.text = "Internal Server Error"
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
        mock_request.return_value = mock_response

        with pytest.raises(AppStoreAPIError) as exc_info:
            client._make_request("GET", "apps/123")

        error = exc_info.value
        assert error.status_code == 500
        assert "Internal Server Error" in str(error)

    @patch("httpx.Client.request")
    def test_make_request_network_error(self, mock_request, client):
        """Test request with network error."""
        mock_request.side_effect = httpx.RequestError("Network error")

        with pytest.raises(AppStoreAPIError, match="Request failed: Network error"):
            client._make_request("GET", "apps/123")

    @patch.object(AppStoreClient, "_make_request")
    def test_get_app_info(self, mock_request, client):
        """Test get_app_info method."""
        expected_response = {"data": {"id": "123", "attributes": {"name": "Test App"}}}
        mock_request.return_value = expected_response

        result = client.get_app_info("123")

        assert result == expected_response
        mock_request.assert_called_once_with("GET", "apps/123")

    @patch.object(AppStoreClient, "_make_request")
    def test_get_app_store_versions(self, mock_request, client):
        """Test get_app_store_versions method."""
        expected_response = {
            "data": [{"id": "456", "attributes": {"versionString": "1.0"}}]
        }
        mock_request.return_value = expected_response

        result = client.get_app_store_versions("123", "IOS")

        assert result == [{"id": "456", "attributes": {"versionString": "1.0"}}]

        mock_request.assert_called_once_with(
            "GET",
            "apps/123/appStoreVersions",
            params={
                "filter[platform]": "IOS",
                "filter[appStoreState]": (
                    "READY_FOR_SALE,PENDING_APPLE_RELEASE,PENDING_CONTRACT,"
                    "PENDING_DEVELOPER_RELEASE"
                ),
            },
        )

    @patch.object(AppStoreClient, "_make_request")
    def test_create_screenshot_set(self, mock_request, client):
        """Test create_screenshot_set method."""
        expected_response = {
            "data": {"id": "screenshot_set_123", "type": "appScreenshotSets"}
        }
        mock_request.return_value = expected_response

        result = client.create_screenshot_set("version_456", "IPHONE_69")

        assert result == expected_response

        expected_data = {
            "data": {
                "type": "appScreenshotSets",
                "attributes": {"screenshotDisplayType": "IPHONE_69"},
                "relationships": {
                    "appStoreVersion": {
                        "data": {"type": "appStoreVersions", "id": "version_456"}
                    }
                },
            }
        }

        mock_request.assert_called_once_with(
            "POST", "appScreenshotSets", data=expected_data
        )

    @patch.object(AppStoreClient, "_make_request")
    def test_create_screenshot_reservation(self, mock_request, client):
        """Test create_screenshot_reservation method."""
        expected_response = {
            "data": {
                "id": "screenshot_789",
                "attributes": {
                    "uploadOperations": [
                        {
                            "url": "https://upload.example.com",
                            "offset": 0,
                            "length": 1024,
                        }
                    ]
                },
            }
        }
        mock_request.return_value = expected_response

        result = client.create_screenshot_reservation("set_123", "screenshot.png", 1024)

        assert result == expected_response

        expected_data = {
            "data": {
                "type": "appScreenshots",
                "attributes": {"fileName": "screenshot.png", "fileSize": 1024},
                "relationships": {
                    "appScreenshotSet": {
                        "data": {"type": "appScreenshotSets", "id": "set_123"}
                    }
                },
            }
        }

        mock_request.assert_called_once_with(
            "POST", "appScreenshots", data=expected_data
        )

    @patch.object(AppStoreClient, "_make_request")
    def test_commit_screenshot_reservation(self, mock_request, client):
        """Test commit_screenshot_reservation method."""
        expected_response = {
            "data": {"id": "screenshot_789", "attributes": {"uploaded": True}}
        }
        mock_request.return_value = expected_response

        result = client.commit_screenshot_reservation("screenshot_789", "abc123def456")

        assert result == expected_response

        expected_data = {
            "data": {
                "type": "appScreenshots",
                "id": "screenshot_789",
                "attributes": {"sourceFileChecksum": "abc123def456", "uploaded": True},
            }
        }

        mock_request.assert_called_once_with(
            "PATCH", "appScreenshots/screenshot_789", data=expected_data
        )

    @patch("httpx.put")
    def test_upload_file_chunk_success(self, mock_put, client):
        """Test successful file chunk upload."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response

        upload_url = "https://upload.example.com/chunk"
        chunk_data = b"test_chunk_data"
        headers = {"Content-Type": "application/octet-stream"}

        client.upload_file_chunk(upload_url, chunk_data, headers)

        mock_put.assert_called_once_with(
            upload_url, content=chunk_data, headers=headers, timeout=httpx.Timeout(60.0)
        )

    @patch("httpx.put")
    def test_upload_file_chunk_failure(self, mock_put, client):
        """Test file chunk upload failure."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_put.return_value = mock_response

        upload_url = "https://upload.example.com/chunk"
        chunk_data = b"test_chunk_data"
        headers = {"Content-Type": "application/octet-stream"}

        with pytest.raises(AppStoreAPIError, match="File upload failed: HTTP 400"):
            client.upload_file_chunk(upload_url, chunk_data, headers)

    @patch("httpx.put")
    def test_upload_file_chunk_network_error(self, mock_put, client):
        """Test file chunk upload with network error."""
        mock_put.side_effect = httpx.RequestError("Network error")

        upload_url = "https://upload.example.com/chunk"
        chunk_data = b"test_chunk_data"
        headers = {"Content-Type": "application/octet-stream"}

        with pytest.raises(
            AppStoreAPIError, match="Upload request failed: Network error"
        ):
            client.upload_file_chunk(upload_url, chunk_data, headers)

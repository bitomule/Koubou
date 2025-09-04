"""App Store Connect API client."""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx

from ..exceptions import KoubouError
from .auth import AppStoreAuth

logger = logging.getLogger(__name__)


class AppStoreAPIError(KoubouError):
    """Error from App Store Connect API."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class AppStoreClient:
    """HTTP client for App Store Connect API."""

    BASE_URL = "https://api.appstoreconnect.apple.com"
    API_VERSION = "v1"

    def __init__(self, auth: AppStoreAuth, timeout: float = 30.0):
        """Initialize API client.

        Args:
            auth: Authenticated App Store Connect client
            timeout: Request timeout in seconds
        """
        self.auth = auth
        self.timeout = timeout
        self.base_url = f"{self.BASE_URL}/{self.API_VERSION}"

        # Create HTTP client with reasonable defaults
        self.client = httpx.Client(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            headers={
                "User-Agent": "koubou-screenshot-uploader/1.0",
                "Accept": "application/json",
            },
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        files: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make authenticated request to App Store Connect API.

        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            data: JSON data for request body
            params: URL query parameters
            files: Files to upload

        Returns:
            Parsed JSON response

        Raises:
            AppStoreAPIError: If request fails
        """
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        headers = self.auth.get_auth_headers()

        # For file uploads, don't set Content-Type header (httpx will set multipart)
        if files:
            headers.pop("Content-Type", None)

        try:
            logger.debug(f"{method} {url}")

            response = self.client.request(
                method=method,
                url=url,
                json=data,
                params=params,
                files=files,
                headers=headers,
            )

            logger.debug(f"Response: {response.status_code}")

            # Handle different response codes
            if 200 <= response.status_code < 300:
                # Success - try to parse JSON
                if response.headers.get("content-type", "").startswith(
                    "application/json"
                ):
                    return response.json()
                else:
                    return {"status": "success", "data": response.text}

            # Error response - try to get error details
            try:
                error_data = response.json() if response.content else {}
            except Exception:
                error_data = {"detail": response.text}

            # Format error message
            if "errors" in error_data:
                errors = error_data["errors"]
                if errors:
                    error_msg = errors[0].get("detail", "Unknown API error")
                    error_code = errors[0].get("code", "UNKNOWN")
                    message = f"{error_code}: {error_msg}"
                else:
                    message = "Unknown API error"
            else:
                message = error_data.get("detail", f"HTTP {response.status_code}")

            raise AppStoreAPIError(
                message=message,
                status_code=response.status_code,
                response_data=error_data,
            )

        except httpx.RequestError as e:
            raise AppStoreAPIError(f"Request failed: {e}") from e
        except Exception as e:
            if isinstance(e, AppStoreAPIError):
                raise
            raise AppStoreAPIError(f"Unexpected error: {e}") from e

    def get_app_info(self, app_id: str) -> Dict[str, Any]:
        """Get app information from App Store Connect.

        Args:
            app_id: App Store Connect app ID

        Returns:
            App information
        """
        return self._make_request("GET", f"apps/{app_id}")

    def get_app_store_versions(
        self, app_id: str, platform: str = "IOS"
    ) -> List[Dict[str, Any]]:
        """Get app store versions for an app.

        Args:
            app_id: App Store Connect app ID
            platform: Platform filter (IOS, MAC_OS, TV_OS)

        Returns:
            List of app store versions
        """
        params = {
            "filter[platform]": platform,
            "filter[appStoreState]": (
                "READY_FOR_SALE,PENDING_APPLE_RELEASE,PENDING_CONTRACT,"
                "PENDING_DEVELOPER_RELEASE"
            ),
        }

        response = self._make_request(
            "GET", f"apps/{app_id}/appStoreVersions", params=params
        )
        return response.get("data", [])

    def get_app_screenshot_sets(self, version_id: str) -> List[Dict[str, Any]]:
        """Get screenshot sets for an app store version.

        Args:
            version_id: App Store version ID

        Returns:
            List of screenshot sets
        """
        response = self._make_request(
            "GET", f"appStoreVersions/{version_id}/appScreenshotSets"
        )
        return response.get("data", [])

    def create_screenshot_set(
        self, version_id: str, display_type: str
    ) -> Dict[str, Any]:
        """Create a new screenshot set for a device display type.

        Args:
            version_id: App Store version ID
            display_type: Device display type (e.g., "IPHONE_69", "IPAD_PRO_129")

        Returns:
            Created screenshot set data
        """
        data = {
            "data": {
                "type": "appScreenshotSets",
                "attributes": {"screenshotDisplayType": display_type},
                "relationships": {
                    "appStoreVersion": {
                        "data": {"type": "appStoreVersions", "id": version_id}
                    }
                },
            }
        }

        return self._make_request("POST", "appScreenshotSets", data=data)

    def delete_screenshots_in_set(self, screenshot_set_id: str) -> None:
        """Delete all screenshots in a screenshot set.

        Args:
            screenshot_set_id: Screenshot set ID
        """
        # Get current screenshots in set
        response = self._make_request(
            "GET", f"appScreenshotSets/{screenshot_set_id}/appScreenshots"
        )
        screenshots = response.get("data", [])

        # Delete each screenshot
        for screenshot in screenshots:
            screenshot_id = screenshot["id"]
            logger.debug(f"Deleting screenshot: {screenshot_id}")
            try:
                self._make_request("DELETE", f"appScreenshots/{screenshot_id}")
            except AppStoreAPIError as e:
                logger.warning(f"Failed to delete screenshot {screenshot_id}: {e}")

    def create_screenshot_reservation(
        self, screenshot_set_id: str, filename: str, file_size: int
    ) -> Dict[str, Any]:
        """Create a screenshot upload reservation.

        Args:
            screenshot_set_id: Screenshot set ID
            filename: Screenshot filename
            file_size: File size in bytes

        Returns:
            Screenshot reservation data with upload instructions
        """
        data = {
            "data": {
                "type": "appScreenshots",
                "attributes": {"fileName": filename, "fileSize": file_size},
                "relationships": {
                    "appScreenshotSet": {
                        "data": {"type": "appScreenshotSets", "id": screenshot_set_id}
                    }
                },
            }
        }

        return self._make_request("POST", "appScreenshots", data=data)

    def commit_screenshot_reservation(
        self, screenshot_id: str, source_file_checksum: str
    ) -> Dict[str, Any]:
        """Commit a screenshot reservation after upload.

        Args:
            screenshot_id: Screenshot ID from reservation
            source_file_checksum: MD5 checksum of uploaded file

        Returns:
            Updated screenshot data
        """
        data = {
            "data": {
                "type": "appScreenshots",
                "id": screenshot_id,
                "attributes": {
                    "sourceFileChecksum": source_file_checksum,
                    "uploaded": True,
                },
            }
        }

        return self._make_request("PATCH", f"appScreenshots/{screenshot_id}", data=data)

    def upload_file_chunk(
        self, upload_url: str, chunk_data: bytes, headers: Dict[str, str]
    ) -> None:
        """Upload a file chunk to the provided URL.

        Args:
            upload_url: Pre-signed upload URL
            chunk_data: File chunk data
            headers: Required headers for upload

        Raises:
            AppStoreAPIError: If upload fails
        """
        try:
            response = httpx.put(
                upload_url,
                content=chunk_data,
                headers=headers,
                timeout=httpx.Timeout(60.0),  # Longer timeout for uploads
            )

            if not (200 <= response.status_code < 300):
                raise AppStoreAPIError(
                    f"File upload failed: HTTP {response.status_code}",
                    status_code=response.status_code,
                )

            logger.debug(f"Uploaded chunk: {len(chunk_data)} bytes")

        except httpx.RequestError as e:
            raise AppStoreAPIError(f"Upload request failed: {e}") from e

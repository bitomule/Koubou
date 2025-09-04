"""Integration tests for end-to-end upload flow."""

import json
from unittest.mock import patch

import pytest
from PIL import Image

from koubou.appstore.auth import AppStoreCredentials
from koubou.appstore.client import AppStoreClient
from koubou.appstore.uploader import (
    DeviceMapper,
    ScreenshotUploader,
    ScreenshotUploadError,
)


@pytest.fixture
def test_credentials(tmp_path):
    """Create test credentials with mock private key."""
    key_file = tmp_path / "AuthKey_TEST123.p8"
    # Create a minimal EC private key for testing (DUMMY KEY - NOT A REAL SECRET)
    key_content = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg7S8j1SWx8KGjTZsW
Tkj3mD7VUE6ZXj+KbhX4d/UgG2ihRANCAASH9j8YHdJ+Y7z8YlYrHK9TsL7fF1S4
F8MJTcLQaR8Y3fH8dP4jX2+8uEH5qJg8yR2c0pKQ7f4nK8KjW1n1s2
-----END PRIVATE KEY-----"""
    key_file.write_text(key_content)

    return AppStoreCredentials(
        key_id="TEST123",
        issuer_id="12345678-1234-1234-1234-123456789012",
        private_key_path=str(key_file),
        app_id="1234567890",
    )


@pytest.fixture
def mock_screenshots_dir(tmp_path):
    """Create mock screenshots directory structure with test images."""
    screenshots_dir = tmp_path / "Screenshots" / "Generated"

    # Create directory structure for different languages and devices
    languages = ["en", "es", "de"]
    devices = [
        "iPhone_15_Pro_-_Natural_Titanium_-_Portrait",
        "iPad_Pro_13_-_M4_-_Silver_-_Portrait",
    ]

    for lang in languages:
        for device in devices:
            device_dir = screenshots_dir / lang / device
            device_dir.mkdir(parents=True)

            # Create test screenshot files
            for i in range(2):  # 2 screenshots per device per language
                screenshot_file = device_dir / f"{i:02d}_test_screenshot.png"

                # Create actual PNG image file with correct dimensions
                if "iPhone" in device:
                    img = Image.new("RGB", (1179, 2556), color="red")
                else:  # iPad
                    img = Image.new("RGB", (2064, 2752), color="blue")

                img.save(screenshot_file, "PNG")

    return screenshots_dir


@pytest.fixture
def mock_frames_json(tmp_path):
    """Create mock Frames.json with device mappings."""
    frames_data = {
        "iPhone": {
            "15 Pro": {
                "Pro": {
                    "Natural Titanium": {
                        "Portrait": {
                            "y": "80",
                            "x": "80",
                            "name": "iPhone 15 Pro - Natural Titanium - Portrait",
                            "appstore_device_type": "IPHONE_69",
                        }
                    }
                }
            }
        },
        "iPad": {
            "iPad Pro 13": {
                "M4": {
                    "Silver": {
                        "Portrait": {
                            "x": "120",
                            "y": "120",
                            "name": "iPad Pro 13 - M4 - Silver - Portrait",
                            "appstore_device_type": "IPAD_PRO_129",
                        }
                    }
                }
            }
        },
    }

    frames_json = tmp_path / "Frames.json"
    with open(frames_json, "w") as f:
        json.dump(frames_data, f)

    return frames_json


class TestEndToEndUploadFlow:
    """Test complete upload workflow from screenshots to App Store Connect."""

    @patch("koubou.appstore.client.AppStoreClient._make_request")
    @patch("koubou.appstore.auth.AppStoreAuth.validate_credentials")
    def test_complete_upload_flow_success(
        self,
        mock_validate_creds,
        mock_make_request,
        test_credentials,
        mock_screenshots_dir,
        mock_frames_json,
    ):
        """Test successful end-to-end upload flow."""
        # Mock credential validation
        mock_validate_creds.return_value = True

        # Track created screenshot sets
        created_sets = {}

        # Mock API responses
        def mock_api_response(method, endpoint, **kwargs):
            if endpoint == "apps/1234567890":
                # App info response
                return {"data": {"attributes": {"name": "Test App"}}}

            elif "appStoreVersions" in endpoint:
                # App store versions response
                return {
                    "data": [
                        {"id": "version123", "attributes": {"versionString": "1.0"}}
                    ]
                }

            elif endpoint == "appStoreVersions/version123/appScreenshotSets":
                # Screenshot sets response - return any created sets
                return {"data": list(created_sets.values())}

            elif endpoint == "appScreenshotSets" and method == "POST":
                # Create screenshot set response
                data = kwargs.get("data", {}).get("data", {})
                display_type = data.get("attributes", {}).get(
                    "screenshotDisplayType", "UNKNOWN"
                )
                set_data = {
                    "id": f"set_{display_type}",
                    "type": "appScreenshotSets",
                    "attributes": {"screenshotDisplayType": display_type},
                }
                created_sets[display_type] = set_data
                return {"data": set_data}

            elif endpoint == "appScreenshots" and method == "POST":
                # Create screenshot reservation response
                return {
                    "data": {
                        "id": "screenshot456",
                        "attributes": {
                            "uploadOperations": [
                                {
                                    "url": "https://upload.example.com/chunk1",
                                    "offset": 0,
                                    "length": 1024,
                                    "requestHeaders": {
                                        "Content-Type": "application/octet-stream"
                                    },
                                }
                            ]
                        },
                    }
                }

            elif "appScreenshots/screenshot456" in endpoint and method == "PATCH":
                # Commit screenshot response
                return {
                    "data": {"id": "screenshot456", "attributes": {"uploaded": True}}
                }

            else:
                return {"data": {}}

        mock_make_request.side_effect = mock_api_response

        # Create uploader with mock frames JSON
        uploader = ScreenshotUploader(test_credentials)
        uploader.device_mapper = DeviceMapper(mock_frames_json)

        # Mock file chunk upload
        with patch.object(AppStoreClient, "upload_file_chunk") as mock_upload_chunk:
            mock_upload_chunk.return_value = None

            # Analyze screenshots
            screenshot_infos = uploader.analyze_screenshots(mock_screenshots_dir)

            # Should find screenshots for both device types across all languages
            assert (
                len(screenshot_infos) == 12
            )  # 2 devices × 3 languages × 2 screenshots each

            # Verify screenshot info
            iphone_screenshots = [
                info for info in screenshot_infos if "iPhone" in info.device_type
            ]
            ipad_screenshots = [
                info for info in screenshot_infos if "iPad" in info.device_type
            ]

            assert len(iphone_screenshots) == 6  # 3 languages × 2 screenshots
            assert len(ipad_screenshots) == 6  # 3 languages × 2 screenshots

            # Verify device types are mapped correctly
            for info in iphone_screenshots:
                assert info.display_type == "IPHONE_69"
                assert info.size == (1179, 2556)

            for info in ipad_screenshots:
                assert info.display_type == "IPAD_PRO_129"
                assert info.size == (2064, 2752)

            # Perform upload
            results = uploader.upload_screenshots(
                screenshot_infos[:2]
            )  # Test with first 2 screenshots

            # Verify results
            assert len(results) == 2
            for result in results:
                assert result.success is True
                assert result.error_message is None

            # Verify API calls were made
            assert mock_make_request.call_count > 0
            assert mock_upload_chunk.call_count == 2  # One chunk upload per screenshot

    @patch("koubou.appstore.client.AppStoreClient._make_request")
    @patch("koubou.appstore.auth.AppStoreAuth.validate_credentials")
    def test_upload_flow_with_api_errors(
        self,
        mock_validate_creds,
        mock_make_request,
        test_credentials,
        mock_screenshots_dir,
        mock_frames_json,
    ):
        """Test upload flow with API errors."""
        from koubou.appstore.client import AppStoreAPIError

        # Mock credential validation
        mock_validate_creds.return_value = True

        # Mock API to return app info but fail on screenshot creation
        def mock_api_response(method, endpoint, **kwargs):
            if endpoint == "apps/1234567890":
                return {"data": {"attributes": {"name": "Test App"}}}
            elif "appStoreVersions" in endpoint:
                return {
                    "data": [
                        {"id": "version123", "attributes": {"versionString": "1.0"}}
                    ]
                }
            elif endpoint == "appStoreVersions/version123/appScreenshotSets":
                return {"data": []}
            elif endpoint == "appScreenshotSets" and method == "POST":
                return {"data": {"id": "set123", "type": "appScreenshotSets"}}
            elif endpoint == "appScreenshots" and method == "POST":
                # Fail screenshot creation
                raise AppStoreAPIError("Screenshot creation failed", status_code=400)
            else:
                return {"data": {}}

        mock_make_request.side_effect = mock_api_response

        # Create uploader
        uploader = ScreenshotUploader(test_credentials)
        uploader.device_mapper = DeviceMapper(mock_frames_json)

        # Analyze screenshots
        screenshot_infos = uploader.analyze_screenshots(mock_screenshots_dir)
        assert len(screenshot_infos) > 0

        # Attempt upload - should handle API errors gracefully
        results = uploader.upload_screenshots(screenshot_infos[:1])

        # Verify error handling
        assert len(results) == 1
        assert results[0].success is False
        assert "Screenshot creation failed" in results[0].error_message

    def test_screenshot_analysis_with_invalid_dimensions(
        self, test_credentials, tmp_path, mock_frames_json
    ):
        """Test screenshot analysis with invalid image dimensions."""
        # Create screenshots with wrong dimensions
        screenshots_dir = tmp_path / "Screenshots" / "Generated"
        device_dir = (
            screenshots_dir / "en" / "iPhone_15_Pro_-_Natural_Titanium_-_Portrait"
        )
        device_dir.mkdir(parents=True)

        # Create image with wrong dimensions
        wrong_size_file = device_dir / "wrong_size.png"
        wrong_img = Image.new("RGB", (800, 600), color="red")  # Wrong size for iPhone
        wrong_img.save(wrong_size_file, "PNG")

        # Create uploader
        uploader = ScreenshotUploader(test_credentials)
        uploader.device_mapper = DeviceMapper(mock_frames_json)

        # Analysis should skip screenshots with wrong dimensions and raise error
        with pytest.raises(ScreenshotUploadError, match="No valid screenshots found"):
            uploader.analyze_screenshots(screenshots_dir)

    def test_screenshot_analysis_no_device_mapping(
        self, test_credentials, tmp_path, mock_frames_json
    ):
        """Test screenshot analysis with unmapped device."""
        # Create screenshots for unknown device
        screenshots_dir = tmp_path / "Screenshots" / "Generated"
        device_dir = screenshots_dir / "en" / "Unknown_Device_Name"
        device_dir.mkdir(parents=True)

        screenshot_file = device_dir / "test.png"
        img = Image.new("RGB", (1000, 1000), color="green")
        img.save(screenshot_file, "PNG")

        # Create uploader
        uploader = ScreenshotUploader(test_credentials)
        uploader.device_mapper = DeviceMapper(mock_frames_json)

        # Analysis should skip screenshots without device mapping and raise error
        with pytest.raises(ScreenshotUploadError, match="No valid screenshots found"):
            uploader.analyze_screenshots(screenshots_dir)


class TestConfigFileIntegration:
    """Test integration with config file operations."""

    def test_credentials_config_file_roundtrip(self, tmp_path):
        """Test creating and loading credentials from config file."""
        from koubou.appstore.auth import create_config_file

        # Create private key file
        key_file = tmp_path / "AuthKey_ROUND123.p8"
        key_file.write_text(
            "-----BEGIN PRIVATE KEY-----\ntest_content\n-----END PRIVATE KEY-----"  # DUMMY KEY
        )

        # Create config file
        config_path = tmp_path / "appstore-config.json"
        credentials_data = {
            "key_id": "ROUND123",
            "issuer_id": "87654321-4321-4321-4321-210987654321",
            "private_key_path": str(key_file),
            "app_id": "1122334455",
        }

        create_config_file(config_path, credentials_data)

        # Verify file was created with correct permissions
        assert config_path.exists()
        assert oct(config_path.stat().st_mode)[-3:] == "600"

        # Load credentials back
        credentials = AppStoreCredentials.from_config_file(config_path)

        assert credentials.key_id == "ROUND123"
        assert credentials.issuer_id == "87654321-4321-4321-4321-210987654321"
        assert credentials.app_id == "1122334455"
        assert credentials.private_key_path == key_file

    def test_relative_path_resolution(self, tmp_path):
        """Test that relative private key paths are resolved correctly."""
        from koubou.appstore.auth import create_config_file

        # Create private key file in same directory as config
        key_file = tmp_path / "AuthKey_REL123.p8"
        key_file.write_text(
            "-----BEGIN PRIVATE KEY-----\ntest_content\n-----END PRIVATE KEY-----"  # DUMMY KEY
        )

        # Create config with relative path
        config_path = tmp_path / "appstore-config.json"
        credentials_data = {
            "key_id": "REL123",
            "issuer_id": "11111111-2222-3333-4444-555555555555",
            "private_key_path": "./AuthKey_REL123.p8",  # Relative path
            "app_id": "9988776655",
        }

        create_config_file(config_path, credentials_data)

        # Load credentials - should resolve relative path
        credentials = AppStoreCredentials.from_config_file(config_path)

        # Private key path should be resolved to absolute path
        assert credentials.private_key_path == key_file
        assert credentials.private_key_path.is_absolute()

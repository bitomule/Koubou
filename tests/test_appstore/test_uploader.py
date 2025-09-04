"""Tests for screenshot uploader."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from koubou.appstore.uploader import (
    DeviceMapper,
    ScreenshotInfo,
    ScreenshotUploader,
    ScreenshotUploadError,
    UploadResult,
)
from koubou.appstore.auth import AppStoreCredentials


class TestDeviceMapper:
    """Test DeviceMapper class."""

    @pytest.fixture
    def mock_frames_json(self, tmp_path):
        """Create a mock Frames.json file."""
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

    def test_init_with_custom_path(self, mock_frames_json):
        """Test initialization with custom Frames.json path."""
        mapper = DeviceMapper(mock_frames_json)
        assert mapper.frames_json_path == mock_frames_json

    def test_init_with_default_path(self):
        """Test initialization with default path."""
        mapper = DeviceMapper()

        # Should point to bundled frames
        # Normalize paths for comparison
        assert str(mapper.frames_json_path).endswith("frames/Frames.json")

    def test_load_device_mappings_success(self, mock_frames_json):
        """Test successful loading of device mappings."""
        mapper = DeviceMapper(mock_frames_json)

        mappings = mapper._load_device_mappings()

        expected_mappings = {
            "iPhone 15 Pro - Natural Titanium - Portrait": "IPHONE_69",
            "iPad Pro 13 - M4 - Silver - Portrait": "IPAD_PRO_129",
        }

        assert mappings == expected_mappings
        assert mapper._device_mappings == expected_mappings

    def test_load_device_mappings_cached(self, mock_frames_json):
        """Test that device mappings are cached."""
        mapper = DeviceMapper(mock_frames_json)

        # First call
        mapper._load_device_mappings()

        # Modify the cached mappings to verify caching works
        mapper._device_mappings["test"] = "TEST_TYPE"

        # Second call should return cached version
        mappings2 = mapper._load_device_mappings()

        assert "test" in mappings2
        assert mappings2["test"] == "TEST_TYPE"

    def test_load_device_mappings_file_not_found(self, tmp_path):
        """Test loading when Frames.json doesn't exist."""
        nonexistent_path = tmp_path / "nonexistent.json"
        mapper = DeviceMapper(nonexistent_path)

        mappings = mapper._load_device_mappings()

        # Should fallback to minimal static mapping
        expected_fallback = {
            "iPhone 15 Pro Portrait": "IPHONE_69",
            "iPhone 16 Pro Portrait": "IPHONE_69",
            "iPad Pro 13 Portrait": "IPAD_PRO_129",
        }

        assert mappings == expected_fallback

    def test_load_device_mappings_invalid_json(self, tmp_path):
        """Test loading with invalid JSON file."""
        invalid_json = tmp_path / "invalid.json"
        invalid_json.write_text("{ invalid json")

        mapper = DeviceMapper(invalid_json)
        mappings = mapper._load_device_mappings()

        # Should fallback to static mapping
        assert "iPhone 15 Pro Portrait" in mappings

    def test_get_display_type(self, mock_frames_json):
        """Test getting display type for device name."""
        mapper = DeviceMapper(mock_frames_json)

        result = mapper.get_display_type("iPhone 15 Pro - Natural Titanium - Portrait")
        assert result == "IPHONE_69"

        result = mapper.get_display_type("iPad Pro 13 - M4 - Silver - Portrait")
        assert result == "IPAD_PRO_129"

        result = mapper.get_display_type("Unknown Device")
        assert result is None

    def test_get_required_dimensions(self):
        """Test getting required dimensions for display types."""
        result = DeviceMapper.get_required_dimensions("IPHONE_69")
        assert result == (1179, 2556)

        result = DeviceMapper.get_required_dimensions("IPAD_PRO_129")
        assert result == (2064, 2752)

        result = DeviceMapper.get_required_dimensions("UNKNOWN_TYPE")
        assert result is None

    @patch("PIL.Image.open")
    def test_validate_screenshot_dimensions_success(self, mock_image_open):
        """Test successful dimension validation."""
        # Mock image with correct dimensions
        mock_image = Mock()
        mock_image.size = (1179, 2556)
        mock_image_open.return_value.__enter__.return_value = mock_image

        result = DeviceMapper.validate_screenshot_dimensions(
            Path("test.png"), "IPHONE_69"
        )

        assert result is True

    @patch("PIL.Image.open")
    def test_validate_screenshot_dimensions_wrong_size(self, mock_image_open):
        """Test dimension validation with wrong size."""
        # Mock image with incorrect dimensions
        mock_image = Mock()
        mock_image.size = (1000, 2000)  # Wrong size
        mock_image_open.return_value.__enter__.return_value = mock_image

        with pytest.raises(ScreenshotUploadError, match="Incorrect dimensions"):
            DeviceMapper.validate_screenshot_dimensions(Path("test.png"), "IPHONE_69")

    @patch("PIL.Image.open")
    def test_validate_screenshot_dimensions_unknown_display_type(self, mock_image_open):
        """Test dimension validation with unknown display type."""
        mock_image = Mock()
        mock_image.size = (1000, 2000)
        mock_image_open.return_value.__enter__.return_value = mock_image

        with pytest.raises(ScreenshotUploadError, match="Unknown display type"):
            DeviceMapper.validate_screenshot_dimensions(
                Path("test.png"), "UNKNOWN_TYPE"
            )

    @patch("PIL.Image.open")
    def test_validate_screenshot_dimensions_image_error(self, mock_image_open):
        """Test dimension validation with image reading error."""
        mock_image_open.side_effect = Exception("Cannot read image")

        with pytest.raises(ScreenshotUploadError, match="Cannot read image"):
            DeviceMapper.validate_screenshot_dimensions(Path("test.png"), "IPHONE_69")


class TestScreenshotInfo:
    """Test ScreenshotInfo dataclass."""

    def test_init_valid(self, tmp_path):
        """Test initialization with valid data."""
        screenshot_file = tmp_path / "test.png"
        screenshot_file.write_bytes(b"fake_image_data")

        info = ScreenshotInfo(
            path=screenshot_file,
            device_type="iPhone 15 Pro - Natural Titanium - Portrait",
            display_type="IPHONE_69",
            size=(1179, 2556),
            file_size=1024,
        )

        assert info.path == screenshot_file
        assert info.device_type == "iPhone 15 Pro - Natural Titanium - Portrait"
        assert info.display_type == "IPHONE_69"
        assert info.size == (1179, 2556)
        assert info.file_size == 1024

    def test_init_missing_file(self, tmp_path):
        """Test initialization with missing file."""
        nonexistent_file = tmp_path / "nonexistent.png"

        with pytest.raises(ScreenshotUploadError, match="Screenshot file not found"):
            ScreenshotInfo(
                path=nonexistent_file,
                device_type="iPhone 15 Pro - Natural Titanium - Portrait",
                display_type="IPHONE_69",
                size=(1179, 2556),
                file_size=1024,
            )

    def test_init_no_display_type(self, tmp_path):
        """Test initialization with no display type mapping."""
        screenshot_file = tmp_path / "test.png"
        screenshot_file.write_bytes(b"fake_image_data")

        with pytest.raises(
            ScreenshotUploadError, match="No display type mapping found"
        ):
            ScreenshotInfo(
                path=screenshot_file,
                device_type="Unknown Device",
                display_type="",  # Empty display type
                size=(1179, 2556),
                file_size=1024,
            )


class TestUploadResult:
    """Test UploadResult dataclass."""

    def test_success_result(self, tmp_path):
        """Test successful upload result."""
        screenshot_path = tmp_path / "test.png"

        result = UploadResult(
            screenshot_path=screenshot_path,
            success=True,
            screenshot_id="screenshot_123",
        )

        assert result.screenshot_path == screenshot_path
        assert result.success is True
        assert result.screenshot_id == "screenshot_123"
        assert result.error_message is None

    def test_failure_result(self, tmp_path):
        """Test failed upload result."""
        screenshot_path = tmp_path / "test.png"

        result = UploadResult(
            screenshot_path=screenshot_path,
            success=False,
            error_message="Upload failed",
        )

        assert result.screenshot_path == screenshot_path
        assert result.success is False
        assert result.error_message == "Upload failed"
        assert result.screenshot_id is None


class TestScreenshotUploader:
    """Test ScreenshotUploader class."""

    @pytest.fixture
    def mock_credentials(self, tmp_path):
        """Create mock credentials."""
        # Create dummy private key file
        key_file = tmp_path / "test_key.p8"
        key_file.write_text(
            "-----BEGIN PRIVATE KEY-----\ntest_content\n-----END PRIVATE KEY-----"
        )

        return AppStoreCredentials(
            key_id="ABC123",
            issuer_id="12345678-1234-1234-1234-123456789012",
            private_key_path=str(key_file),
            app_id="987654321",
        )

    @pytest.fixture
    def uploader(self, mock_credentials):
        """Create uploader instance."""
        return ScreenshotUploader(mock_credentials)

    def test_init(self, mock_credentials):
        """Test uploader initialization."""
        uploader = ScreenshotUploader(mock_credentials)

        assert uploader.credentials == mock_credentials
        assert isinstance(uploader.device_mapper, DeviceMapper)

    @patch("PIL.Image.open")
    def test_analyze_screenshots_success(self, mock_image_open, uploader, tmp_path):
        """Test successful screenshot analysis."""
        # Setup directory structure: Screenshots/Generated/{language}/
        # {device}/screenshot.png
        screenshots_dir = tmp_path / "Screenshots" / "Generated"
        device_dir = (
            screenshots_dir / "en" / "iPhone_15_Pro_-_Natural_Titanium_-_Portrait"
        )
        device_dir.mkdir(parents=True)

        screenshot_file = device_dir / "01_test_screenshot.png"
        screenshot_file.write_bytes(b"fake_png_data")

        # Mock PIL Image
        mock_image = Mock()
        mock_image.size = (1179, 2556)  # Correct dimensions for IPHONE_69
        mock_image_open.return_value.__enter__.return_value = mock_image

        # Mock device mapper to return valid mapping
        uploader.device_mapper.get_display_type = Mock(return_value="IPHONE_69")

        with patch.object(
            DeviceMapper, "validate_screenshot_dimensions", return_value=True
        ):
            result = uploader.analyze_screenshots(screenshots_dir)

        assert len(result) == 1
        screenshot_info = result[0]
        assert screenshot_info.path == screenshot_file
        assert (
            screenshot_info.device_type == "iPhone 15 Pro - Natural Titanium - Portrait"
        )
        assert screenshot_info.display_type == "IPHONE_69"
        assert screenshot_info.size == (1179, 2556)

    def test_analyze_screenshots_no_files(self, uploader, tmp_path):
        """Test screenshot analysis with no PNG files."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(ScreenshotUploadError, match="No PNG screenshots found"):
            uploader.analyze_screenshots(empty_dir)

    @patch("PIL.Image.open")
    def test_analyze_screenshots_no_device_mapping(
        self, mock_image_open, uploader, tmp_path
    ):
        """Test screenshot analysis with no device mapping."""
        screenshots_dir = tmp_path / "Screenshots" / "Generated"
        device_dir = screenshots_dir / "en" / "Unknown_Device"
        device_dir.mkdir(parents=True)

        screenshot_file = device_dir / "test.png"
        screenshot_file.write_bytes(b"fake_png_data")

        # Mock device mapper to return None (no mapping found)
        uploader.device_mapper.get_display_type = Mock(return_value=None)

        # Should skip screenshots without device mapping and raise error
        with pytest.raises(ScreenshotUploadError, match="No valid screenshots found"):
            uploader.analyze_screenshots(screenshots_dir)

    def test_calculate_md5_checksum(self, uploader, tmp_path):
        """Test MD5 checksum calculation."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        checksum = uploader._calculate_md5_checksum(test_file)

        # Expected MD5 of "Hello, World!"
        expected_checksum = "65a8e27d8879283831b664bd8b7f0ad4"
        assert checksum == expected_checksum

    @patch.object(ScreenshotUploader, "_calculate_md5_checksum")
    def test_upload_file_chunks(self, mock_checksum, uploader, tmp_path):
        """Test file chunk upload."""
        # Create test file
        test_file = tmp_path / "test.png"
        test_content = b"test_file_content"
        test_file.write_bytes(test_content)

        # Mock client
        mock_client = Mock()

        # Define upload operations
        upload_operations = [
            {
                "url": "https://upload.example.com/chunk1",
                "offset": 0,
                "length": 8,
                "requestHeaders": {"Content-Type": "application/octet-stream"},
            },
            {
                "url": "https://upload.example.com/chunk2",
                "offset": 8,
                "length": 9,
                "requestHeaders": {"Content-Type": "application/octet-stream"},
            },
        ]

        uploader._upload_file_chunks(mock_client, test_file, upload_operations)

        # Verify chunks were uploaded
        assert mock_client.upload_file_chunk.call_count == 2

        # Check first chunk
        call1_args = mock_client.upload_file_chunk.call_args_list[0]
        assert call1_args[0][0] == "https://upload.example.com/chunk1"  # URL
        assert call1_args[0][1] == b"test_fil"  # First 8 bytes

        # Check second chunk
        call2_args = mock_client.upload_file_chunk.call_args_list[1]
        assert call2_args[0][0] == "https://upload.example.com/chunk2"  # URL
        assert call2_args[0][1] == b"e_content"  # Remaining 9 bytes

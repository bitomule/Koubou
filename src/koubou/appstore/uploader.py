"""Screenshot upload manager for App Store Connect."""

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)

from ..exceptions import KoubouError
from .auth import AppStoreCredentials, AppStoreAuth
from .client import AppStoreAPIError, AppStoreClient

logger = logging.getLogger(__name__)
console = Console()


class ScreenshotUploadError(KoubouError):
    """Error during screenshot upload process."""

    pass


@dataclass
class ScreenshotInfo:
    """Information about a screenshot file."""

    path: Path
    device_type: str
    display_type: str  # App Store Connect display type (e.g., "IPHONE_69")
    size: Tuple[int, int]
    file_size: int

    def __post_init__(self):
        """Validate screenshot info after creation."""
        if not self.path.exists():
            raise ScreenshotUploadError(f"Screenshot file not found: {self.path}")

        if not self.display_type:
            raise ScreenshotUploadError(
                f"No display type mapping found for device: {self.device_type}"
            )


@dataclass
class UploadResult:
    """Result of screenshot upload operation."""

    screenshot_path: Path
    success: bool
    error_message: Optional[str] = None
    screenshot_id: Optional[str] = None


class DeviceMapper:
    """Maps koubou device names to App Store Connect display types."""

    def __init__(self, frames_json_path: Optional[Path] = None):
        """Initialize device mapper.

        Args:
            frames_json_path: Path to Frames.json file. If None, uses bundled version.
        """
        self.frames_json_path = frames_json_path or self._get_bundled_frames_path()
        self._device_mappings = None

    def _get_bundled_frames_path(self) -> Path:
        """Get path to bundled Frames.json."""
        # Navigate up from current file to find frames directory
        current_file = Path(__file__)
        koubou_root = current_file.parent.parent
        return koubou_root / "frames" / "Frames.json"

    def _load_device_mappings(self) -> Dict[str, str]:
        """Load device mappings from Frames.json file."""
        if self._device_mappings is not None:
            return self._device_mappings

        try:
            import json

            with open(self.frames_json_path) as f:
                frames_data = json.load(f)

            mappings = {}

            def extract_mappings(data, parent_key=""):
                """Recursively extract device mappings from nested JSON."""
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, dict):
                            # Check if this level has a 'name' and
                            # 'appstore_device_type'
                            if (
                                "name" in value and
                                "appstore_device_type" in value
                            ):
                                device_name = value["name"]
                                appstore_type = value["appstore_device_type"]
                                mappings[device_name] = appstore_type
                                logger.debug(
                                    f"Found mapping: {device_name} -> {appstore_type}"
                                )
                            else:
                                # Recurse into nested structure
                                extract_mappings(value, key)

            extract_mappings(frames_data)

            logger.info(
                f"Loaded {len(mappings)} device mappings from {self.frames_json_path}"
            )
            self._device_mappings = mappings
            return mappings

        except Exception as e:
            logger.error(
                f"Failed to load device mappings from {self.frames_json_path}: {e}"
            )
            # Fallback to minimal static mapping
            self._device_mappings = {
                "iPhone 15 Pro Portrait": "IPHONE_69",
                "iPhone 16 Pro Portrait": "IPHONE_69",
                "iPad Pro 13 Portrait": "IPAD_PRO_129",
            }
            return self._device_mappings

    # Required dimensions for each display type (width x height)
    REQUIRED_DIMENSIONS = {
        "IPHONE_69": (1179, 2556),  # 6.9" iPhone (iPhone 15 Pro and later)
        "IPAD_PRO_129": (2064, 2752),  # 12.9" iPad Pro (13-inch)
    }

    def get_display_type(self, device_name: str) -> Optional[str]:
        """Get App Store Connect display type for device name.

        Args:
            device_name: Koubou device name

        Returns:
            App Store Connect display type or None if not found
        """
        mappings = self._load_device_mappings()
        return mappings.get(device_name)

    @classmethod
    def get_required_dimensions(cls, display_type: str) -> Optional[Tuple[int, int]]:
        """Get required dimensions for display type.

        Args:
            display_type: App Store Connect display type

        Returns:
            (width, height) tuple or None if not found
        """
        return cls.REQUIRED_DIMENSIONS.get(display_type)

    @classmethod
    def validate_screenshot_dimensions(
        cls, image_path: Path, display_type: str
    ) -> bool:
        """Validate that screenshot has correct dimensions for display type.

        Args:
            image_path: Path to screenshot image
            display_type: App Store Connect display type

        Returns:
            True if dimensions are correct

        Raises:
            ScreenshotUploadError: If validation fails
        """
        try:
            with Image.open(image_path) as img:
                actual_size = img.size
        except Exception as e:
            raise ScreenshotUploadError(f"Cannot read image {image_path}: {e}") from e

        required_size = cls.get_required_dimensions(display_type)
        if not required_size:
            raise ScreenshotUploadError(f"Unknown display type: {display_type}")

        if actual_size != required_size:
            raise ScreenshotUploadError(
                f"Incorrect dimensions for {display_type}. "
                f"Expected {required_size}, got {actual_size} in {image_path.name}"
            )

        return True


class ScreenshotUploader:
    """Manages screenshot uploads to App Store Connect."""

    def __init__(self, credentials: AppStoreCredentials):
        """Initialize uploader.

        Args:
            credentials: App Store Connect credentials
        """
        self.credentials = credentials
        self.device_mapper = DeviceMapper()

    def analyze_screenshots(self, screenshots_dir: Path) -> List[ScreenshotInfo]:
        """Analyze generated screenshots and prepare upload info.

        Args:
            screenshots_dir: Directory containing generated screenshots

        Returns:
            List of screenshot information
        """
        screenshot_infos = []

        # Find all PNG files in the directory structure
        png_files = list(screenshots_dir.rglob("*.png"))

        if not png_files:
            raise ScreenshotUploadError(
                f"No PNG screenshots found in {screenshots_dir}"
            )

        for screenshot_path in png_files:
            try:
                # Extract device info from path structure
                # Expected: Screenshots/Generated/{language}/{device_name}/
                # screenshot.png
                path_parts = screenshot_path.parts

                # Find device name in path (should be second to last part)
                if len(path_parts) >= 2:
                    device_name = path_parts[-2].replace("_", " ")
                else:
                    logger.warning(
                        f"Cannot determine device from path: "
                        f"{screenshot_path}"
                    )
                    continue

                # Get display type mapping
                display_type = self.device_mapper.get_display_type(device_name)
                if not display_type:
                    logger.warning(
                        f"No display type mapping for device: {device_name}"
                    )
                    continue

                # Get image dimensions and file size
                with Image.open(screenshot_path) as img:
                    size = img.size
                file_size = screenshot_path.stat().st_size

                # Validate dimensions
                try:
                    self.device_mapper.validate_screenshot_dimensions(
                        screenshot_path, display_type
                    )
                except ScreenshotUploadError as e:
                    logger.error(str(e))
                    continue

                screenshot_info = ScreenshotInfo(
                    path=screenshot_path,
                    device_type=device_name,
                    display_type=display_type,
                    size=size,
                    file_size=file_size,
                )

                screenshot_infos.append(screenshot_info)
                logger.debug(
                    f"Analyzed screenshot: {screenshot_path.name} -> {display_type}"
                )

            except Exception as e:
                logger.error(f"Failed to analyze screenshot {screenshot_path}: {e}")
                continue

        if not screenshot_infos:
            raise ScreenshotUploadError("No valid screenshots found for upload")

        return screenshot_infos

    def _calculate_md5_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of a file.

        Args:
            file_path: Path to file

        Returns:
            MD5 checksum as hex string
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _upload_file_chunks(
        self,
        client: AppStoreClient,
        screenshot_path: Path,
        upload_operations: List[Dict],
    ) -> None:
        """Upload file in chunks according to upload operations.

        Args:
            client: App Store Connect API client
            screenshot_path: Path to screenshot file
            upload_operations: List of upload operation instructions
        """
        with open(screenshot_path, "rb") as f:
            file_data = f.read()

        # Process each upload operation
        for operation in upload_operations:
            url = operation["url"]
            offset = operation["offset"]
            length = operation["length"]
            headers = operation.get("requestHeaders", {})

            # Extract chunk data
            chunk_data = file_data[offset : offset + length]

            # Upload chunk
            client.upload_file_chunk(url, chunk_data, headers)

    def upload_screenshots(
        self, screenshot_infos: List[ScreenshotInfo], replace_existing: bool = True
    ) -> List[UploadResult]:
        """Upload screenshots to App Store Connect.

        Args:
            screenshot_infos: List of screenshots to upload
            replace_existing: Whether to replace existing screenshots

        Returns:
            List of upload results
        """
        results = []

        with AppStoreClient(auth=AppStoreAuth(self.credentials)) as client:
            try:
                # Get app info and current version
                app_info = client.get_app_info(self.credentials.app_id)
                app_name = app_info["data"]["attributes"]["name"]
                console.print(f"📱 Uploading to app: [bold]{app_name}[/bold]")

                # Get current app store version
                versions = client.get_app_store_versions(self.credentials.app_id)
                if not versions:
                    raise ScreenshotUploadError("No app store versions found for app")

                # Use the first version (usually current/latest)
                version = versions[0]
                version_id = version["id"]
                version_string = version["attributes"]["versionString"]
                console.print(f"📦 Version: [bold]{version_string}[/bold]")

                # Group screenshots by display type
                screenshots_by_type: Dict[str, List[ScreenshotInfo]] = {}
                for info in screenshot_infos:
                    if info.display_type not in screenshots_by_type:
                        screenshots_by_type[info.display_type] = []
                    screenshots_by_type[info.display_type].append(info)

                # Upload screenshots for each display type
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeElapsedColumn(),
                    console=console,
                ) as progress:

                    total_screenshots = len(screenshot_infos)
                    main_task = progress.add_task(
                        "Uploading screenshots...", total=total_screenshots
                    )

                    for display_type, screenshots in screenshots_by_type.items():
                        progress.console.print(
                            f"🖼️  Processing {display_type}: "
                            f"{len(screenshots)} screenshots"
                        )

                        # Get or create screenshot set for this display type
                        screenshot_sets = client.get_app_screenshot_sets(version_id)
                        screenshot_set = None

                        for sset in screenshot_sets:
                            sset_display_type = sset.get("attributes", {}).get(
                                "screenshotDisplayType"
                            )
                            if sset_display_type == display_type:
                                screenshot_set = sset
                                break

                        if not screenshot_set:
                            # Create new screenshot set
                            screenshot_set = client.create_screenshot_set(
                                version_id, display_type
                            )["data"]
                            console.print(
                                f"✅ Created screenshot set for {display_type}"
                            )

                        screenshot_set_id = screenshot_set["id"]

                        # Clear existing screenshots if replacing
                        if replace_existing:
                            client.delete_screenshots_in_set(screenshot_set_id)
                            console.print(
                                f"🗑️  Cleared existing screenshots for {display_type}"
                            )

                        # Upload each screenshot in this set
                        for screenshot_info in screenshots:
                            try:
                                # Create upload reservation
                                reservation = client.create_screenshot_reservation(
                                    screenshot_set_id,
                                    screenshot_info.path.name,
                                    screenshot_info.file_size,
                                )

                                reservation_data = reservation["data"]
                                screenshot_id = reservation_data["id"]
                                upload_operations = reservation_data["attributes"][
                                    "uploadOperations"
                                ]

                                # Upload file chunks
                                self._upload_file_chunks(
                                    client, screenshot_info.path, upload_operations
                                )

                                # Calculate checksum and commit
                                checksum = self._calculate_md5_checksum(
                                    screenshot_info.path
                                )
                                client.commit_screenshot_reservation(
                                    screenshot_id, checksum
                                )

                                # Record success
                                results.append(
                                    UploadResult(
                                        screenshot_path=screenshot_info.path,
                                        success=True,
                                        screenshot_id=screenshot_id,
                                    )
                                )

                                console.print(
                                    f"✅ Uploaded: {screenshot_info.path.name}"
                                )

                            except Exception as e:
                                error_msg = f"Upload failed: {e}"
                                logger.error(
                                    f"Failed to upload {screenshot_info.path}: {e}"
                                )
                                results.append(
                                    UploadResult(
                                        screenshot_path=screenshot_info.path,
                                        success=False,
                                        error_message=error_msg,
                                    )
                                )
                                console.print(
                                    f"❌ Failed: {screenshot_info.path.name} "
                                    f"- {error_msg}"
                                )

                            finally:
                                progress.update(main_task, advance=1)

            except (AppStoreAPIError, ScreenshotUploadError) as e:
                # API or upload errors - mark all remaining as failed
                for info in screenshot_infos:
                    if not any(r.screenshot_path == info.path for r in results):
                        results.append(
                            UploadResult(
                                screenshot_path=info.path,
                                success=False,
                                error_message=str(e),
                            )
                        )
                raise

        return results

"""Automatic dependency analysis for asset tracking and change detection."""

import logging
from pathlib import Path
from typing import Dict, List, Set, Union

from .config import ProjectConfig

logger = logging.getLogger(__name__)


class AssetDependency:
    """Represents a dependency relationship between a screenshot and an asset."""

    def __init__(self, screenshot_id: str, asset_path: str, asset_type: str = "image"):
        """Initialize asset dependency.

        Args:
            screenshot_id: ID of the screenshot that depends on the asset
            asset_path: Path to the asset file
            asset_type: Type of asset (image, etc.)
        """
        self.screenshot_id = screenshot_id
        self.asset_path = asset_path
        self.asset_type = asset_type
        self.resolved_path: Union[Path, None] = None
        self.last_modified: Union[float, None] = None

    def resolve_path(self, config_dir: Path) -> bool:
        """Resolve the asset path relative to config directory.

        Args:
            config_dir: Directory containing the config file

        Returns:
            True if path was successfully resolved and file exists
        """
        # Handle absolute paths
        if Path(self.asset_path).is_absolute():
            resolved = Path(self.asset_path)
        else:
            # Resolve relative to config directory
            resolved = config_dir / self.asset_path

        if resolved.exists():
            self.resolved_path = resolved
            try:
                self.last_modified = resolved.stat().st_mtime
                return True
            except OSError as e:
                logger.warning(f"Could not get modification time for {resolved}: {e}")
                return False
        else:
            logger.warning(f"Asset not found: {resolved}")
            return False

    def has_changed(self) -> bool:
        """Check if the asset file has been modified since last check.

        Returns:
            True if the asset has been modified
        """
        if not self.resolved_path or not self.resolved_path.exists():
            return False

        try:
            current_mtime = self.resolved_path.stat().st_mtime
            if self.last_modified is None:
                self.last_modified = current_mtime
                return False

            changed = current_mtime > self.last_modified
            if changed:
                self.last_modified = current_mtime
            return changed
        except OSError as e:
            logger.warning(
                f"Could not check modification time for {self.resolved_path}: {e}"
            )
            return False


class DependencyAnalyzer:
    """Analyzes project configuration to build dependency graphs."""

    def __init__(self) -> None:
        """Initialize the dependency analyzer."""
        self.dependencies: List[AssetDependency] = []
        self._screenshot_to_assets: Dict[str, List[AssetDependency]] = {}
        self._asset_to_screenshots: Dict[str, List[str]] = {}

    def analyze_project(self, config: ProjectConfig, config_dir: Path) -> None:
        """Analyze a project configuration to build dependency graph.

        Args:
            config: Project configuration to analyze
            config_dir: Directory containing the config file
        """
        self.dependencies = []
        self._screenshot_to_assets = {}
        self._asset_to_screenshots = {}

        # Analyze each screenshot for asset dependencies
        for screenshot_id, screenshot_def in config.screenshots.items():
            screenshot_assets = []

            # Scan content items for asset references
            for content_item in screenshot_def.content:
                if content_item.type == "image" and content_item.asset:
                    # Create dependency
                    dependency = AssetDependency(
                        screenshot_id=screenshot_id,
                        asset_path=content_item.asset,
                        asset_type="image",
                    )

                    # Try to resolve the asset path
                    if dependency.resolve_path(config_dir):
                        self.dependencies.append(dependency)
                        screenshot_assets.append(dependency)

                        # Update mappings
                        asset_key = str(dependency.resolved_path)
                        if asset_key not in self._asset_to_screenshots:
                            self._asset_to_screenshots[asset_key] = []
                        self._asset_to_screenshots[asset_key].append(screenshot_id)
                    else:
                        logger.warning(
                            f"Could not resolve asset {content_item.asset} "
                            f"for screenshot {screenshot_id}"
                        )

            self._screenshot_to_assets[screenshot_id] = screenshot_assets

        logger.info(
            f"Analyzed {len(self.dependencies)} asset dependencies across "
            f"{len(config.screenshots)} screenshots"
        )

    def get_screenshot_assets(self, screenshot_id: str) -> List[AssetDependency]:
        """Get all assets that a screenshot depends on.

        Args:
            screenshot_id: Screenshot ID to query

        Returns:
            List of asset dependencies for the screenshot
        """
        return self._screenshot_to_assets.get(screenshot_id, [])

    def get_asset_screenshots(self, asset_path: Union[str, Path]) -> List[str]:
        """Get all screenshots that depend on a given asset.

        Args:
            asset_path: Path to the asset file

        Returns:
            List of screenshot IDs that depend on the asset
        """
        asset_key = str(Path(asset_path).resolve())
        return self._asset_to_screenshots.get(asset_key, [])

    def get_all_asset_paths(self) -> Set[Path]:
        """Get all asset paths that are being tracked.

        Returns:
            Set of all asset file paths
        """
        return {
            dep.resolved_path
            for dep in self.dependencies
            if dep.resolved_path is not None
        }

    def check_asset_changes(self) -> Dict[str, List[str]]:
        """Check all tracked assets for modifications.

        Returns:
            Dictionary mapping changed asset paths to affected screenshot IDs
        """
        changed_assets = {}

        for dependency in self.dependencies:
            if dependency.has_changed():
                asset_path = str(dependency.resolved_path)
                if asset_path not in changed_assets:
                    changed_assets[asset_path] = []
                changed_assets[asset_path].append(dependency.screenshot_id)

        return changed_assets

    def get_dependency_summary(self) -> Dict[str, Union[int, Dict]]:
        """Get a summary of the current dependency state.

        Returns:
            Dictionary with dependency statistics and mappings
        """
        return {
            "total_dependencies": len(self.dependencies),
            "total_screenshots": len(self._screenshot_to_assets),
            "total_assets": len(self._asset_to_screenshots),
            "screenshot_to_assets": {
                screenshot_id: [dep.asset_path for dep in deps]
                for screenshot_id, deps in self._screenshot_to_assets.items()
            },
            "asset_to_screenshots": dict(self._asset_to_screenshots),
        }

    def validate_all_assets(self) -> Dict[str, List[str]]:
        """Validate that all tracked assets still exist.

        Returns:
            Dictionary mapping missing asset paths to affected screenshot IDs
        """
        missing_assets = {}

        for dependency in self.dependencies:
            if not dependency.resolved_path or not dependency.resolved_path.exists():
                asset_path = dependency.asset_path
                if asset_path not in missing_assets:
                    missing_assets[asset_path] = []
                missing_assets[asset_path].append(dependency.screenshot_id)

        if missing_assets:
            logger.warning(f"Found {len(missing_assets)} missing assets")

        return missing_assets

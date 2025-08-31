"""Live screenshot generation with selective regeneration capabilities."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml
from rich.console import Console

from .config import ProjectConfig
from .config_tree import ConfigDiffer
from .dependency_analyzer import DependencyAnalyzer
from .exceptions import ConfigurationError, KoubouError
from .generator import ScreenshotGenerator

logger = logging.getLogger(__name__)


class LiveGenerationResult:
    """Result of a live generation cycle."""

    def __init__(self) -> None:
        """Initialize empty result."""
        self.regenerated_screenshots: List[str] = []
        self.skipped_screenshots: List[str] = []
        self.failed_screenshots: Dict[str, str] = {}  # screenshot_id -> error
        self.config_errors: List[str] = []
        self.total_time: float = 0.0

    @property
    def success_count(self) -> int:
        """Number of successfully regenerated screenshots."""
        return len(self.regenerated_screenshots)

    @property
    def error_count(self) -> int:
        """Number of failed screenshots."""
        return len(self.failed_screenshots)

    @property
    def has_errors(self) -> bool:
        """Whether any errors occurred."""
        return bool(self.config_errors or self.failed_screenshots)


class LiveScreenshotGenerator:
    """Handles live screenshot generation with change detection and selective
    rebuilding."""

    def __init__(self, config_file: Path):
        """Initialize live generator.

        Args:
            config_file: Path to the YAML configuration file
        """
        self.config_file = config_file.resolve()
        self.config_dir = self.config_file.parent

        # Core components
        self.generator = ScreenshotGenerator()
        self.config_differ = ConfigDiffer()
        self.dependency_analyzer = DependencyAnalyzer()
        self.console = Console()

        # State
        self.current_config: Optional[ProjectConfig] = None
        self._last_successful_generation: Dict[str, float] = {}

        logger.info(f"Initialized live generator for: {self.config_file}")

    def load_config(self) -> Optional[ProjectConfig]:
        """Load and parse the configuration file.

        Returns:
            Parsed project configuration or None if loading failed
        """
        try:
            with open(self.config_file, "r") as f:
                config_data = yaml.safe_load(f)

            # Validate and parse configuration
            config = ProjectConfig(**config_data)
            logger.debug("Successfully loaded and validated configuration")
            return config

        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_file}")
            return None
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}")
            return None
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            return None

    def initial_generation(self) -> LiveGenerationResult:
        """Perform initial generation of all screenshots.

        Returns:
            Generation result with details of what was processed
        """
        result = LiveGenerationResult()

        # Load configuration
        config = self.load_config()
        if not config:
            result.config_errors.append("Failed to load configuration")
            return result

        self.current_config = config

        # Analyze dependencies
        self.dependency_analyzer.analyze_project(config, self.config_dir)

        # Initialize config differ with current config
        config_dict = self._config_to_dict(config)
        self.config_differ.detect_changes(config_dict)

        # Generate all screenshots
        logger.info("Starting initial generation of all screenshots")

        for screenshot_id in config.screenshots.keys():
            try:
                self._generate_single_screenshot(config, screenshot_id)
                result.regenerated_screenshots.append(screenshot_id)
                logger.info(f"✅ Generated: {screenshot_id}")
            except Exception as e:
                result.failed_screenshots[screenshot_id] = str(e)
                logger.error(f"❌ Failed to generate {screenshot_id}: {e}")

        logger.info(
            f"Initial generation complete: {result.success_count} success, "
            f"{result.error_count} errors"
        )

        return result

    def handle_file_changes(self, changed_files: Set[Path]) -> LiveGenerationResult:
        """Handle file system changes and regenerate affected screenshots.

        Args:
            changed_files: Set of file paths that have changed

        Returns:
            Generation result with details of what was processed
        """
        result = LiveGenerationResult()

        # Separate config changes from asset changes
        config_changed = self.config_file in changed_files
        asset_changes = changed_files - {self.config_file}

        affected_screenshots = set()

        # Handle config changes
        if config_changed:
            logger.info("📝 Config file changed, analyzing impact...")
            config_affected = self._handle_config_changes(result)
            affected_screenshots.update(config_affected)

        # Handle asset changes
        if asset_changes:
            logger.info(
                f"🖼️  {len(asset_changes)} asset(s) changed, analyzing impact..."
            )
            asset_affected = self._handle_asset_changes(asset_changes)
            affected_screenshots.update(asset_affected)

        # Regenerate affected screenshots
        if affected_screenshots and self.current_config:
            if "*ALL*" in affected_screenshots:
                # Global change affects everything
                screenshot_ids = list(self.current_config.screenshots.keys())
                logger.info("🌍 Global change detected, regenerating all screenshots")
            else:
                # Handle defaults marker
                screenshot_ids = []
                for screenshot_id in affected_screenshots:
                    if screenshot_id == "*DEFAULTS*":
                        # Add screenshots that use default settings
                        screenshot_ids.extend(self._get_screenshots_using_defaults())
                    else:
                        screenshot_ids.append(screenshot_id)

                # Remove duplicates and filter out screenshots that don't exist
                screenshot_ids = list(set(screenshot_ids))
                screenshot_ids = [
                    sid
                    for sid in screenshot_ids
                    if sid in self.current_config.screenshots
                ]

            logger.info(f"🔄 Regenerating {len(screenshot_ids)} affected screenshot(s)")

            for screenshot_id in screenshot_ids:
                try:
                    self._generate_single_screenshot(self.current_config, screenshot_id)
                    result.regenerated_screenshots.append(screenshot_id)
                    logger.info(f"✅ Regenerated: {screenshot_id}")
                except Exception as e:
                    result.failed_screenshots[screenshot_id] = str(e)
                    logger.error(f"❌ Failed to regenerate {screenshot_id}: {e}")
        else:
            logger.info("No screenshots affected by changes")

        return result

    def _handle_config_changes(self, result: LiveGenerationResult) -> Set[str]:
        """Handle configuration file changes.

        Args:
            result: Result object to accumulate errors in

        Returns:
            Set of affected screenshot IDs
        """
        # Try to load new config
        new_config = self.load_config()
        if not new_config:
            result.config_errors.append("Failed to reload configuration after change")
            return set()

        # Convert to dictionary for comparison
        new_config_dict = self._config_to_dict(new_config)

        # Detect changes
        change_result = self.config_differ.detect_changes(new_config_dict)

        if not change_result["has_changes"]:
            logger.debug("Config file changed but no meaningful differences detected")
            return set()

        # Update current config
        self.current_config = new_config

        # Re-analyze dependencies with new config
        self.dependency_analyzer.analyze_project(new_config, self.config_dir)

        # Log changes
        changes = change_result["changes"]
        logger.debug(
            f"Config changes: {len(changes['added'])} added, "
            f"{len(changes['changed'])} changed, {len(changes['removed'])} removed"
        )

        return change_result["affected_screenshots"]

    def _handle_asset_changes(self, asset_files: Set[Path]) -> Set[str]:
        """Handle asset file changes.

        Args:
            asset_files: Set of changed asset file paths

        Returns:
            Set of affected screenshot IDs
        """
        affected_screenshots = set()

        for asset_path in asset_files:
            screenshot_ids = self.dependency_analyzer.get_asset_screenshots(asset_path)
            affected_screenshots.update(screenshot_ids)

            if screenshot_ids:
                logger.debug(
                    f"Asset {asset_path} affects screenshots: {screenshot_ids}"
                )

        return affected_screenshots

    def _generate_single_screenshot(
        self, config: ProjectConfig, screenshot_id: str
    ) -> None:
        """Generate a single screenshot by ID.

        Args:
            config: Project configuration
            screenshot_id: ID of screenshot to generate

        Raises:
            KoubouError: If screenshot generation fails
        """
        if screenshot_id not in config.screenshots:
            raise ConfigurationError(
                f"Screenshot ID '{screenshot_id}' not found in config"
            )

        # Create a temporary project config with just this screenshot
        single_screenshot_config = ProjectConfig(
            project=config.project,
            devices=config.devices,
            defaults=config.defaults,
            screenshots={screenshot_id: config.screenshots[screenshot_id]},
        )

        # Generate the screenshot
        result_paths = self.generator.generate_project(
            single_screenshot_config, self.config_dir
        )

        if not result_paths:
            raise KoubouError(f"Failed to generate screenshot '{screenshot_id}'")

        # Update last generation time
        import time

        self._last_successful_generation[screenshot_id] = time.time()

    def _get_screenshots_using_defaults(self) -> List[str]:
        """Get screenshot IDs that use default settings.

        Returns:
            List of screenshot IDs that rely on defaults
        """
        if not self.current_config:
            return []

        using_defaults = []

        for screenshot_id, screenshot_def in self.current_config.screenshots.items():
            # Check if screenshot has custom background
            if not screenshot_def.background:
                using_defaults.append(screenshot_id)

        return using_defaults

    def _config_to_dict(self, config: ProjectConfig) -> Dict:
        """Convert ProjectConfig to dictionary for diffing.

        Args:
            config: Project configuration to convert

        Returns:
            Dictionary representation of the config
        """
        # Convert to dict using Pydantic's model_dump
        return config.model_dump()

    def get_dependency_summary(self) -> Dict:
        """Get summary of current dependency state.

        Returns:
            Dictionary with dependency information
        """
        return self.dependency_analyzer.get_dependency_summary()

    def get_asset_paths(self) -> Set[Path]:
        """Get all asset paths that should be watched.

        Returns:
            Set of asset file paths to monitor
        """
        return self.dependency_analyzer.get_all_asset_paths()

    def validate_assets(self) -> Dict[str, List[str]]:
        """Validate that all assets exist.

        Returns:
            Dictionary of missing assets and affected screenshots
        """
        return self.dependency_analyzer.validate_all_assets()

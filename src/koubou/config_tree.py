"""Config tree flattening and diffing for live editing functionality."""

import logging
from typing import Any, Dict, Set, Union

logger = logging.getLogger(__name__)


class ConfigTree:
    """Handles flattening config dictionaries to path-value pairs for diffing."""

    @staticmethod
    def flatten(config_dict: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten a nested dictionary to dot-separated paths.

        Args:
            config_dict: Nested dictionary to flatten
            prefix: Path prefix for nested calls

        Returns:
            Flattened dictionary with dot-separated keys

        Example:
            {"project": {"name": "App"}} -> {"project.name": "App"}
            {"screenshots": [{"name": "test"}]} -> {"screenshots[0].name": "test"}
        """
        result = {}

        for key, value in config_dict.items():
            current_path = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                # Recursively flatten nested dictionaries
                nested = ConfigTree.flatten(value, current_path)
                result.update(nested)
            elif isinstance(value, list):
                # Handle lists with indexed paths
                for i, item in enumerate(value):
                    item_path = f"{current_path}[{i}]"
                    if isinstance(item, dict):
                        nested = ConfigTree.flatten(item, item_path)
                        result.update(nested)
                    else:
                        result[item_path] = item
            else:
                # Store primitive values directly
                result[current_path] = value

        return result

    @staticmethod
    def diff(old_tree: Dict[str, Any], new_tree: Dict[str, Any]) -> Dict[str, Any]:
        """Find differences between two flattened config trees.

        Args:
            old_tree: Previous flattened config
            new_tree: Current flattened config

        Returns:
            Dictionary containing added, changed, and removed paths
        """
        old_keys = set(old_tree.keys())
        new_keys = set(new_tree.keys())

        # Find different types of changes
        added_keys = new_keys - old_keys
        removed_keys = old_keys - new_keys
        common_keys = old_keys & new_keys

        # Find changed values in common keys
        changed_keys = {key for key in common_keys if old_tree[key] != new_tree[key]}

        changes = {
            "added": {key: new_tree[key] for key in added_keys},
            "changed": {
                key: {"old": old_tree[key], "new": new_tree[key]}
                for key in changed_keys
            },
            "removed": {key: old_tree[key] for key in removed_keys},
        }

        return changes

    @staticmethod
    def get_affected_screenshots(changes: Dict[str, Any]) -> Set[str]:
        """Determine which screenshots are affected by config changes.

        Args:
            changes: Change dictionary from diff()

        Returns:
            Set of screenshot IDs that need regeneration
        """
        affected_screenshots = set()

        # Get all changed paths
        all_changed_paths = set()
        all_changed_paths.update(changes.get("added", {}).keys())
        all_changed_paths.update(changes.get("changed", {}).keys())
        all_changed_paths.update(changes.get("removed", {}).keys())

        for path in all_changed_paths:
            if ConfigTree._is_global_change(path):
                # Global changes affect all screenshots
                return {"*ALL*"}  # Special marker for all screenshots
            elif ConfigTree._is_defaults_change(path):
                # Defaults changes affect screenshots that don't override those defaults
                affected_screenshots.add("*DEFAULTS*")  # Special marker
            else:
                # Extract screenshot ID from path
                screenshot_id = ConfigTree._extract_screenshot_id(path)
                if screenshot_id:
                    affected_screenshots.add(screenshot_id)

        return affected_screenshots

    @staticmethod
    def _is_global_change(path: str) -> bool:
        """Check if a path represents a global change affecting all screenshots."""
        global_prefixes = [
            "project.name",
            "project.output_dir",
            "devices",  # Device changes affect all screenshots
        ]
        return any(path.startswith(prefix) for prefix in global_prefixes)

    @staticmethod
    def _is_defaults_change(path: str) -> bool:
        """Check if a path represents a change to default settings."""
        return path.startswith("defaults.")

    @staticmethod
    def _extract_screenshot_id(path: str) -> Union[str, None]:
        """Extract screenshot ID from a config path.

        Args:
            path: Config path like "screenshots.welcome_screen.content[0].size"

        Returns:
            Screenshot ID or None if not a screenshot-specific path
        """
        if not path.startswith("screenshots."):
            return None

        # Extract the screenshot ID after "screenshots."
        parts = path.split(".")
        if len(parts) < 2:
            return None

        return parts[1]  # The screenshot ID


class ConfigDiffer:
    """High-level interface for config diffing and change detection."""

    def __init__(self) -> None:
        """Initialize the config differ."""
        self.tree = ConfigTree()
        self._last_config: Dict[str, Any] = {}
        self._last_flattened: Dict[str, Any] = {}

    def detect_changes(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Detect changes between the last config and new config.

        Args:
            new_config: New configuration dictionary

        Returns:
            Change detection results with affected screenshots
        """
        # Flatten the new config
        new_flattened = self.tree.flatten(new_config)

        # If this is the first config, no changes
        if not self._last_flattened:
            self._last_config = new_config
            self._last_flattened = new_flattened
            return {
                "changes": {"added": {}, "changed": {}, "removed": {}},
                "affected_screenshots": set(),
                "has_changes": False,
            }

        # Find differences
        changes = self.tree.diff(self._last_flattened, new_flattened)
        affected_screenshots = self.tree.get_affected_screenshots(changes)

        # Check if there are any actual changes
        has_changes = bool(changes["added"] or changes["changed"] or changes["removed"])

        # Update stored config
        self._last_config = new_config
        self._last_flattened = new_flattened

        result = {
            "changes": changes,
            "affected_screenshots": affected_screenshots,
            "has_changes": has_changes,
        }

        logger.debug(
            f"Config changes detected: {len(changes['added'])} added, "
            f"{len(changes['changed'])} changed, {len(changes['removed'])} removed"
        )
        logger.debug(f"Affected screenshots: {affected_screenshots}")

        return result

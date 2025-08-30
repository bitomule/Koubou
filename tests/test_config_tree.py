"""Tests for config tree flattening and diffing functionality."""

from koubou.config_tree import ConfigDiffer, ConfigTree


class TestConfigTree:
    """Tests for ConfigTree functionality."""

    def test_flatten_simple_dict(self):
        """Test flattening a simple dictionary."""
        config = {
            "project": {"name": "Test App", "output_dir": "output"},
            "devices": ["iPhone 15 Pro"],
        }

        result = ConfigTree.flatten(config)

        assert result["project.name"] == "Test App"
        assert result["project.output_dir"] == "output"
        assert result["devices[0]"] == "iPhone 15 Pro"

    def test_flatten_nested_screenshots(self):
        """Test flattening screenshot configurations."""
        config = {
            "screenshots": {
                "welcome_screen": {
                    "content": [
                        {
                            "type": "text",
                            "content": "Welcome",
                            "position": ["50%", "20%"],
                        }
                    ]
                }
            }
        }

        result = ConfigTree.flatten(config)

        assert result["screenshots.welcome_screen.content[0].type"] == "text"
        assert result["screenshots.welcome_screen.content[0].content"] == "Welcome"
        assert result["screenshots.welcome_screen.content[0].position[0]"] == "50%"
        assert result["screenshots.welcome_screen.content[0].position[1]"] == "20%"

    def test_flatten_empty_dict(self):
        """Test flattening an empty dictionary."""
        config = {}
        result = ConfigTree.flatten(config)
        assert result == {}

    def test_flatten_deeply_nested(self):
        """Test flattening deeply nested structures."""
        config = {"level1": {"level2": {"level3": [{"level4": {"value": "deep"}}]}}}

        result = ConfigTree.flatten(config)
        assert result["level1.level2.level3[0].level4.value"] == "deep"

    def test_diff_no_changes(self):
        """Test diffing identical configs."""
        old_config = {"project": {"name": "App"}}
        new_config = {"project": {"name": "App"}}

        old_flat = ConfigTree.flatten(old_config)
        new_flat = ConfigTree.flatten(new_config)

        changes = ConfigTree.diff(old_flat, new_flat)

        assert changes["added"] == {}
        assert changes["changed"] == {}
        assert changes["removed"] == {}

    def test_diff_added_keys(self):
        """Test diffing with added keys."""
        old_config = {"project": {"name": "App"}}
        new_config = {"project": {"name": "App", "version": "1.0"}}

        old_flat = ConfigTree.flatten(old_config)
        new_flat = ConfigTree.flatten(new_config)

        changes = ConfigTree.diff(old_flat, new_flat)

        assert changes["added"] == {"project.version": "1.0"}
        assert changes["changed"] == {}
        assert changes["removed"] == {}

    def test_diff_changed_values(self):
        """Test diffing with changed values."""
        old_config = {"project": {"name": "Old App"}}
        new_config = {"project": {"name": "New App"}}

        old_flat = ConfigTree.flatten(old_config)
        new_flat = ConfigTree.flatten(new_config)

        changes = ConfigTree.diff(old_flat, new_flat)

        assert changes["added"] == {}
        assert changes["changed"] == {
            "project.name": {"old": "Old App", "new": "New App"}
        }
        assert changes["removed"] == {}

    def test_diff_removed_keys(self):
        """Test diffing with removed keys."""
        old_config = {"project": {"name": "App", "version": "1.0"}}
        new_config = {"project": {"name": "App"}}

        old_flat = ConfigTree.flatten(old_config)
        new_flat = ConfigTree.flatten(new_config)

        changes = ConfigTree.diff(old_flat, new_flat)

        assert changes["added"] == {}
        assert changes["changed"] == {}
        assert changes["removed"] == {"project.version": "1.0"}

    def test_get_affected_screenshots_global_change(self):
        """Test identifying global changes that affect all screenshots."""
        changes = {"added": {"project.name": "New App"}, "changed": {}, "removed": {}}

        affected = ConfigTree.get_affected_screenshots(changes)
        assert "*ALL*" in affected

    def test_get_affected_screenshots_defaults_change(self):
        """Test identifying defaults changes."""
        changes = {
            "added": {},
            "changed": {"defaults.background.color": {"old": "#fff", "new": "#000"}},
            "removed": {},
        }

        affected = ConfigTree.get_affected_screenshots(changes)
        assert "*DEFAULTS*" in affected

    def test_get_affected_screenshots_specific_screenshot(self):
        """Test identifying specific screenshot changes."""
        changes = {
            "added": {},
            "changed": {
                "screenshots.welcome_screen.content[0].text": {
                    "old": "Hi",
                    "new": "Hello",
                }
            },
            "removed": {},
        }

        affected = ConfigTree.get_affected_screenshots(changes)
        assert "welcome_screen" in affected
        assert "*ALL*" not in affected

    def test_extract_screenshot_id(self):
        """Test extracting screenshot IDs from config paths."""
        assert (
            ConfigTree._extract_screenshot_id(
                "screenshots.welcome_screen.content[0].text"
            )
            == "welcome_screen"
        )
        assert (
            ConfigTree._extract_screenshot_id(
                "screenshots.features_screen.background.color"
            )
            == "features_screen"
        )
        assert ConfigTree._extract_screenshot_id("project.name") is None
        assert ConfigTree._extract_screenshot_id("defaults.background") is None

    def test_is_global_change(self):
        """Test identifying global changes."""
        assert ConfigTree._is_global_change("project.name") is True
        assert ConfigTree._is_global_change("project.output_dir") is True
        assert ConfigTree._is_global_change("devices[0]") is True
        assert (
            ConfigTree._is_global_change("screenshots.welcome_screen.content") is False
        )

    def test_is_defaults_change(self):
        """Test identifying defaults changes."""
        assert ConfigTree._is_defaults_change("defaults.background.color") is True
        assert ConfigTree._is_defaults_change("defaults.device") is True
        assert ConfigTree._is_defaults_change("project.name") is False
        assert (
            ConfigTree._is_defaults_change("screenshots.welcome_screen.content")
            is False
        )


class TestConfigDiffer:
    """Tests for ConfigDiffer functionality."""

    def test_initial_config_no_changes(self):
        """Test that the first config load shows no changes."""
        differ = ConfigDiffer()
        config = {"project": {"name": "App"}}

        result = differ.detect_changes(config)

        assert result["has_changes"] is False
        assert result["affected_screenshots"] == set()

    def test_detect_simple_change(self):
        """Test detecting simple configuration changes."""
        differ = ConfigDiffer()

        # Load initial config
        config1 = {"project": {"name": "App"}}
        differ.detect_changes(config1)

        # Load changed config
        config2 = {"project": {"name": "New App"}}
        result = differ.detect_changes(config2)

        assert result["has_changes"] is True
        assert "*ALL*" in result["affected_screenshots"]
        assert result["changes"]["changed"]["project.name"]["old"] == "App"
        assert result["changes"]["changed"]["project.name"]["new"] == "New App"

    def test_detect_screenshot_specific_change(self):
        """Test detecting screenshot-specific changes."""
        differ = ConfigDiffer()

        # Load initial config
        config1 = {
            "screenshots": {
                "welcome_screen": {"content": [{"type": "text", "content": "Hello"}]}
            }
        }
        differ.detect_changes(config1)

        # Load changed config
        config2 = {
            "screenshots": {
                "welcome_screen": {
                    "content": [{"type": "text", "content": "Hi there!"}]
                }
            }
        }
        result = differ.detect_changes(config2)

        assert result["has_changes"] is True
        assert "welcome_screen" in result["affected_screenshots"]
        assert "*ALL*" not in result["affected_screenshots"]

    def test_no_changes_detected(self):
        """Test when no actual changes are detected."""
        differ = ConfigDiffer()

        config = {"project": {"name": "App"}}
        differ.detect_changes(config)

        # Same config again
        result = differ.detect_changes(config)

        assert result["has_changes"] is False
        assert result["affected_screenshots"] == set()

    def test_multiple_changes(self):
        """Test detecting multiple simultaneous changes."""
        differ = ConfigDiffer()

        # Initial config
        config1 = {
            "project": {"name": "App"},
            "defaults": {"background": {"color": "#fff"}},
            "screenshots": {
                "screen1": {"content": [{"text": "Hello"}]},
                "screen2": {"content": [{"text": "World"}]},
            },
        }
        differ.detect_changes(config1)

        # Multiple changes
        config2 = {
            "project": {"name": "App"},  # No change
            "defaults": {"background": {"color": "#000"}},  # Defaults change
            "screenshots": {
                "screen1": {"content": [{"text": "Hi"}]},  # Specific change
                "screen2": {"content": [{"text": "World"}]},  # No change
            },
        }
        result = differ.detect_changes(config2)

        assert result["has_changes"] is True
        assert "*DEFAULTS*" in result["affected_screenshots"]
        assert "screen1" in result["affected_screenshots"]
        assert len(result["changes"]["changed"]) >= 2

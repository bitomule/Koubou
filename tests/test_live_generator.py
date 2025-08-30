"""Tests for live generator functionality."""

from pathlib import Path
from unittest.mock import patch

import yaml
from PIL import Image

from koubou.live_generator import LiveGenerationResult, LiveScreenshotGenerator


class TestLiveGenerationResult:
    """Tests for LiveGenerationResult."""

    def test_empty_result(self):
        """Test empty result initialization."""
        result = LiveGenerationResult()

        assert result.regenerated_screenshots == []
        assert result.skipped_screenshots == []
        assert result.failed_screenshots == {}
        assert result.config_errors == []
        assert result.total_time == 0.0
        assert result.success_count == 0
        assert result.error_count == 0
        assert result.has_errors is False

    def test_result_with_successes(self):
        """Test result with successful regenerations."""
        result = LiveGenerationResult()
        result.regenerated_screenshots = ["screen1", "screen2"]

        assert result.success_count == 2
        assert result.error_count == 0
        assert result.has_errors is False

    def test_result_with_errors(self):
        """Test result with errors."""
        result = LiveGenerationResult()
        result.failed_screenshots = {"screen1": "Error message"}
        result.config_errors = ["Config error"]

        assert result.success_count == 0
        assert result.error_count == 1
        assert result.has_errors is True

    def test_result_mixed(self):
        """Test result with mixed success and errors."""
        result = LiveGenerationResult()
        result.regenerated_screenshots = ["screen1"]
        result.failed_screenshots = {"screen2": "Error"}
        result.skipped_screenshots = ["screen3"]

        assert result.success_count == 1
        assert result.error_count == 1
        assert result.has_errors is True


class TestLiveScreenshotGenerator:
    """Tests for LiveScreenshotGenerator."""

    def create_test_config_file(self, tmp_path) -> tuple[Path, Path]:
        """Create a test config file and assets."""
        # Create assets directory
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()

        # Create test images
        image1_path = assets_dir / "welcome.png"
        image2_path = assets_dir / "features.png"

        test_image = Image.new("RGB", (200, 400), "red")
        test_image.save(image1_path)
        test_image.save(image2_path)

        # Create config file
        config_data = {
            "project": {"name": "Test Project", "output_dir": "output"},
            "defaults": {"background": {"type": "solid", "colors": ["#ffffff"]}},
            "screenshots": {
                "welcome_screen": {
                    "content": [
                        {
                            "type": "text",
                            "content": "Welcome",
                            "position": ["50%", "20%"],
                            "size": 32,
                            "color": "#000000",
                        },
                        {
                            "type": "image",
                            "asset": "assets/welcome.png",
                            "position": ["50%", "60%"],
                            "scale": 0.8,
                        },
                    ]
                },
                "features_screen": {
                    "background": {"type": "solid", "colors": ["#eeeeee"]},
                    "content": [
                        {
                            "type": "text",
                            "content": "Features",
                            "position": ["50%", "20%"],
                            "size": 32,
                            "color": "#333333",
                        },
                        {
                            "type": "image",
                            "asset": "assets/features.png",
                            "position": ["50%", "60%"],
                            "scale": 0.8,
                        },
                    ],
                },
            },
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False)

        return config_file, tmp_path

    def test_generator_creation(self, tmp_path):
        """Test creating a live generator."""
        config_file, _ = self.create_test_config_file(tmp_path)

        generator = LiveScreenshotGenerator(config_file)

        assert generator.config_file == config_file.resolve()
        assert generator.config_dir == config_file.parent
        assert generator.current_config is None

    def test_load_config_success(self, tmp_path):
        """Test successful config loading."""
        config_file, _ = self.create_test_config_file(tmp_path)
        generator = LiveScreenshotGenerator(config_file)

        config = generator.load_config()

        assert config is not None
        assert config.project.name == "Test Project"
        assert len(config.screenshots) == 2
        assert "welcome_screen" in config.screenshots
        assert "features_screen" in config.screenshots

    def test_load_config_nonexistent_file(self, tmp_path):
        """Test loading non-existent config file."""
        config_file = tmp_path / "nonexistent.yaml"
        generator = LiveScreenshotGenerator(config_file)

        config = generator.load_config()
        assert config is None

    def test_load_config_invalid_yaml(self, tmp_path):
        """Test loading invalid YAML file."""
        config_file = tmp_path / "invalid.yaml"
        with open(config_file, "w") as f:
            f.write("invalid: yaml: content: [unclosed")

        generator = LiveScreenshotGenerator(config_file)
        config = generator.load_config()
        assert config is None

    def test_load_config_invalid_schema(self, tmp_path):
        """Test loading YAML with invalid schema."""
        config_data = {
            "project": {"name": "Test"},
            # Missing required fields
        }

        config_file = tmp_path / "invalid_schema.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        generator = LiveScreenshotGenerator(config_file)
        config = generator.load_config()
        assert config is None

    @patch("koubou.live_generator.LiveScreenshotGenerator._generate_single_screenshot")
    def test_initial_generation_success(self, mock_generate, tmp_path):
        """Test successful initial generation."""
        config_file, _ = self.create_test_config_file(tmp_path)
        generator = LiveScreenshotGenerator(config_file)

        # Mock successful generation
        mock_generate.return_value = None

        result = generator.initial_generation()

        assert result.success_count == 2  # Two screenshots
        assert result.error_count == 0
        assert result.has_errors is False
        assert "welcome_screen" in result.regenerated_screenshots
        assert "features_screen" in result.regenerated_screenshots

        # Should have called generate for each screenshot
        assert mock_generate.call_count == 2

    @patch("koubou.live_generator.LiveScreenshotGenerator._generate_single_screenshot")
    def test_initial_generation_with_errors(self, mock_generate, tmp_path):
        """Test initial generation with some failures."""
        config_file, _ = self.create_test_config_file(tmp_path)
        generator = LiveScreenshotGenerator(config_file)

        # Mock one success, one failure
        def side_effect(*args, **kwargs):
            screenshot_id = args[1]  # Second argument is screenshot_id
            if screenshot_id == "welcome_screen":
                return None  # Success
            else:
                raise Exception("Generation failed")

        mock_generate.side_effect = side_effect

        result = generator.initial_generation()

        assert result.success_count == 1
        assert result.error_count == 1
        assert result.has_errors is True
        assert "welcome_screen" in result.regenerated_screenshots
        assert "features_screen" in result.failed_screenshots

    def test_initial_generation_config_load_failure(self, tmp_path):
        """Test initial generation when config loading fails."""
        # Create generator with non-existent config
        config_file = tmp_path / "nonexistent.yaml"
        generator = LiveScreenshotGenerator(config_file)

        result = generator.initial_generation()

        assert result.success_count == 0
        assert result.error_count == 0
        assert result.has_errors is True
        assert "Failed to load configuration" in result.config_errors

    def test_handle_config_changes(self, tmp_path):
        """Test handling configuration file changes."""
        config_file, config_dir = self.create_test_config_file(tmp_path)
        generator = LiveScreenshotGenerator(config_file)

        # Load initial config
        generator.initial_generation()

        # Modify config file
        config_data = {
            "project": {
                "name": "Updated Test Project",  # Changed
                "output_dir": "output",
            },
            "screenshots": {
                "welcome_screen": {
                    "content": [
                        {
                            "type": "text",
                            "content": "Updated Welcome",  # Changed
                            "position": ["50%", "20%"],
                            "size": 32,
                            "color": "#000000",
                        }
                    ]
                }
            },
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Handle file changes
        changed_files = {config_file}

        with patch.object(generator, "_generate_single_screenshot") as mock_gen:
            result = generator.handle_file_changes(changed_files)

            # Should regenerate all screenshots due to global change
            assert mock_gen.call_count == 1  # Only one screenshot in updated config
            assert "welcome_screen" in result.regenerated_screenshots

    def test_handle_asset_changes(self, tmp_path):
        """Test handling asset file changes."""
        config_file, config_dir = self.create_test_config_file(tmp_path)
        generator = LiveScreenshotGenerator(config_file)

        # Load initial config
        generator.initial_generation()

        # Simulate asset change
        asset_file = config_dir / "assets" / "welcome.png"
        changed_files = {asset_file}

        with patch.object(generator, "_generate_single_screenshot") as mock_gen:
            result = generator.handle_file_changes(changed_files)

            # Should regenerate only the screenshot that uses this asset
            assert mock_gen.call_count == 1
            assert "welcome_screen" in result.regenerated_screenshots
            assert "features_screen" not in result.regenerated_screenshots

    def test_get_dependency_summary(self, tmp_path):
        """Test getting dependency summary."""
        config_file, _ = self.create_test_config_file(tmp_path)
        generator = LiveScreenshotGenerator(config_file)

        # Load initial config
        generator.initial_generation()

        summary = generator.get_dependency_summary()

        assert summary["total_dependencies"] == 2  # Two images
        assert summary["total_screenshots"] == 2
        assert "welcome_screen" in summary["screenshot_to_assets"]
        assert "features_screen" in summary["screenshot_to_assets"]

    def test_get_asset_paths(self, tmp_path):
        """Test getting asset paths for watching."""
        config_file, config_dir = self.create_test_config_file(tmp_path)
        generator = LiveScreenshotGenerator(config_file)

        # Load initial config
        generator.initial_generation()

        asset_paths = generator.get_asset_paths()

        assert len(asset_paths) == 2
        path_names = {path.name for path in asset_paths}
        assert "welcome.png" in path_names
        assert "features.png" in path_names

    def test_validate_assets_all_exist(self, tmp_path):
        """Test asset validation when all assets exist."""
        config_file, _ = self.create_test_config_file(tmp_path)
        generator = LiveScreenshotGenerator(config_file)

        # Load initial config
        generator.initial_generation()

        missing_assets = generator.validate_assets()
        assert missing_assets == {}

    def test_validate_assets_some_missing(self, tmp_path):
        """Test asset validation with missing assets."""
        config_file, config_dir = self.create_test_config_file(tmp_path)
        generator = LiveScreenshotGenerator(config_file)

        # Load initial config
        generator.initial_generation()

        # Remove one asset
        welcome_asset = config_dir / "assets" / "welcome.png"
        welcome_asset.unlink()

        missing_assets = generator.validate_assets()

        assert len(missing_assets) == 1
        assert "assets/welcome.png" in missing_assets
        assert "welcome_screen" in missing_assets["assets/welcome.png"]

    def test_config_to_dict(self, tmp_path):
        """Test converting ProjectConfig to dictionary."""
        config_file, _ = self.create_test_config_file(tmp_path)
        generator = LiveScreenshotGenerator(config_file)

        config = generator.load_config()
        config_dict = generator._config_to_dict(config)

        assert isinstance(config_dict, dict)
        assert "project" in config_dict
        assert "screenshots" in config_dict
        assert config_dict["project"]["name"] == "Test Project"

    def test_get_screenshots_using_defaults(self, tmp_path):
        """Test identifying screenshots that use default settings."""
        config_file, _ = self.create_test_config_file(tmp_path)
        generator = LiveScreenshotGenerator(config_file)

        # Load initial config
        generator.initial_generation()

        screenshots_using_defaults = generator._get_screenshots_using_defaults()

        # welcome_screen uses defaults (no custom background)
        # features_screen has custom background
        assert "welcome_screen" in screenshots_using_defaults
        assert "features_screen" not in screenshots_using_defaults

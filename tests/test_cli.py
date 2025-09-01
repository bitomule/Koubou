"""Tests for CLI functionality."""

import tempfile
from pathlib import Path

import yaml
from PIL import Image
from typer.testing import CliRunner

from koubou.cli import app


class TestCLI:
    """Tests for command-line interface."""

    def setup_method(self):
        """Setup test method."""
        self.runner = CliRunner()
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create test source image
        self.source_image_path = self.temp_dir / "source.png"
        source_image = Image.new("RGBA", (200, 400), (255, 0, 0, 255))
        source_image.save(self.source_image_path)

    def teardown_method(self):
        """Cleanup after test."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_version_flag(self):
        """Test --version flag."""
        result = self.runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "Koubou" in result.stdout

    def test_version_short_flag(self):
        """Test -v flag."""
        result = self.runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        assert "Koubou" in result.stdout

    def test_create_config_option(self):
        """Test --create-config option."""
        config_path = self.temp_dir / "test_config.yaml"

        result = self.runner.invoke(
            app, ["--create-config", str(config_path), "--name", "Test Project"]
        )

        assert result.exit_code == 0
        assert config_path.exists()

        # Verify config content matches new ProjectConfig format
        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert config["project"]["name"] == "Test Project"
        assert config["project"]["output_dir"] == "Screenshots/Generated"
        assert "devices" in config
        assert "screenshots" in config
        assert (
            len(config["screenshots"]) == 3
        )  # Updated CLI generates 3 sample screenshots

    def test_help_when_no_arguments(self):
        """Test help is shown when no arguments provided."""
        result = self.runner.invoke(app, [])
        assert result.exit_code == 0
        assert "Koubou" in result.stdout or "help" in result.stdout.lower()

    def test_direct_config_command(self):
        """Test direct config file command."""
        # Create test configuration
        config_data = {
            "project": {
                "name": "CLI Test Project",
                "output_dir": str(self.temp_dir / "output"),
            },
            "devices": ["iPhone 15 Pro Portrait"],
            "screenshots": {
                "cli_test_screenshot": {
                    "content": [
                        {
                            "type": "image",
                            "asset": str(self.source_image_path),
                            "position": ["50%", "50%"],
                            "scale": 1.0,
                        }
                    ],
                }
            },
        }

        config_path = self.temp_dir / "test_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        result = self.runner.invoke(app, ["generate", str(config_path), "--verbose"])

        assert result.exit_code == 0

        # Check that output was created
        output_dir = self.temp_dir / "output"
        assert output_dir.exists()

        # Should have generated a screenshot
        output_files = list(output_dir.glob("*.png"))
        assert len(output_files) >= 1

    def test_nonexistent_config(self):
        """Test direct command with nonexistent config."""
        result = self.runner.invoke(app, ["generate", "nonexistent_config.yaml"])

        assert result.exit_code == 1
        assert "not found" in result.stdout

    def test_invalid_config(self):
        """Test direct command with invalid config."""
        # Create invalid config (missing required fields)
        config_data = {
            "project": {"name": "Invalid Project"},
            "screenshots": [
                {
                    "name": "Invalid Screenshot"
                    # Missing required content field
                }
            ],
        }

        config_path = self.temp_dir / "invalid_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        result = self.runner.invoke(app, ["generate", str(config_path)])

        assert result.exit_code == 1
        assert "Invalid configuration" in result.stdout

    def test_config_with_output_dir(self):
        """Test config file with output directory specified in YAML."""
        # Create test configuration
        config_data = {
            "project": {
                "name": "Output Dir Test",
                "output_dir": str(self.temp_dir / "yaml_output"),
            },
            "devices": ["iPhone 15 Pro Portrait"],
            "screenshots": {
                "test_screenshot": {
                    "content": [
                        {
                            "type": "image",
                            "asset": str(self.source_image_path),
                            "position": ["50%", "50%"],
                            "scale": 1.0,
                        }
                    ],
                }
            },
        }

        config_path = self.temp_dir / "test_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        result = self.runner.invoke(app, ["generate", str(config_path)])

        assert result.exit_code == 0

        yaml_output = self.temp_dir / "yaml_output"
        assert yaml_output.exists()

        # Should have generated a screenshot in YAML-specified directory
        output_files = list(yaml_output.glob("*.png"))
        assert len(output_files) >= 1

    def test_list_frames_command(self):
        """Test list-frames command."""
        result = self.runner.invoke(app, ["list-frames"])

        assert result.exit_code == 0
        assert "Available Device Frames" in result.stdout
        assert "Found" in result.stdout
        assert "frames" in result.stdout

    def test_list_frames_with_search(self):
        """Test list-frames command with search filter."""
        result = self.runner.invoke(app, ["list-frames", "iPhone"])

        assert result.exit_code == 0
        assert "iPhone" in result.stdout
        assert "Available Device Frames" in result.stdout

    def test_list_frames_specific_search(self):
        """Test list-frames command with specific search."""
        result = self.runner.invoke(app, ["list-frames", "15 Pro"])

        assert result.exit_code == 0
        assert "15 Pro" in result.stdout or "Found 0 frames" in result.stdout
        assert "Available Device Frames" in result.stdout

    def test_list_frames_no_results(self):
        """Test list-frames command with search that returns no results."""
        result = self.runner.invoke(app, ["list-frames", "NonexistentDevice123"])

        assert result.exit_code == 0
        assert "No frames found matching" in result.stdout

    def test_list_frames_verbose(self):
        """Test list-frames command with verbose flag."""
        result = self.runner.invoke(app, ["list-frames", "--verbose"])

        assert result.exit_code == 0
        assert "Available Device Frames" in result.stdout

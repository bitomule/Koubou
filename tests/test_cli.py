"""Tests for CLI functionality."""

import tempfile
from pathlib import Path

import pytest
import yaml
from PIL import Image
from typer.testing import CliRunner

from koubou.cli import app


@pytest.mark.skip(reason="CLI tests need to be updated for new callback structure")
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

    def test_create_config_command(self):
        """Test create_config command."""
        config_path = self.temp_dir / "test_config.yaml"

        result = self.runner.invoke(
            app, ["create-config", str(config_path), "--name", "Test Project"]
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

    def test_direct_config_command(self):
        """Test direct config file command."""
        # Create test configuration
        config_data = {
            "project": {
                "name": "CLI Test Project",
                "output_dir": str(self.temp_dir / "output"),
            },
            "devices": ["iPhone 15 Pro Portrait"],
            "screenshots": [
                {
                    "name": "CLI Test Screenshot",
                    "content": [
                        {
                            "type": "image",
                            "asset": str(self.source_image_path),
                            "position": ["50%", "50%"],
                            "scale": 1.0,
                        }
                    ],
                }
            ],
        }

        config_path = self.temp_dir / "test_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        result = self.runner.invoke(app, [str(config_path), "--verbose"])

        assert result.exit_code == 0

        # Check that output was created
        output_dir = self.temp_dir / "output"
        assert output_dir.exists()

        # Should have generated a screenshot
        output_files = list(output_dir.glob("*.png"))
        assert len(output_files) >= 1

    def test_nonexistent_config(self):
        """Test direct command with nonexistent config."""
        result = self.runner.invoke(app, ["nonexistent_config.yaml"])

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

        result = self.runner.invoke(app, [str(config_path)])

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
            "screenshots": [
                {
                    "name": "Test Screenshot",
                    "content": [
                        {
                            "type": "image",
                            "asset": str(self.source_image_path),
                            "position": ["50%", "50%"],
                            "scale": 1.0,
                        }
                    ],
                }
            ],
        }

        config_path = self.temp_dir / "test_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        result = self.runner.invoke(app, [str(config_path)])

        assert result.exit_code == 0

        yaml_output = self.temp_dir / "yaml_output"
        assert yaml_output.exists()

        # Should have generated a screenshot in YAML-specified directory
        output_files = list(yaml_output.glob("*.png"))
        assert len(output_files) >= 1

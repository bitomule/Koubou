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

    def test_version_command(self):
        """Test version command."""
        result = self.runner.invoke(app, ["version"])
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

    def test_list_frames_command(self):
        """Test list-frames command."""
        # Create mock frame directory
        frame_dir = self.temp_dir / "frames"
        frame_dir.mkdir()

        # Create mock frame
        frame_image = Image.new("RGBA", (300, 600), (128, 128, 128, 255))
        frame_path = frame_dir / "Test Frame.png"
        frame_image.save(frame_path)

        result = self.runner.invoke(app, ["list-frames", "--frames", str(frame_dir)])

        assert result.exit_code == 0
        assert "Test Frame" in result.stdout

    def test_generate_command(self):
        """Test generate command."""
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

        result = self.runner.invoke(app, ["generate", str(config_path), "--verbose"])

        assert result.exit_code == 0

        # Check that output was created
        output_dir = self.temp_dir / "output"
        assert output_dir.exists()

        # Should have generated a screenshot
        output_files = list(output_dir.glob("*.png"))
        assert len(output_files) >= 1

    def test_generate_nonexistent_config(self):
        """Test generate command with nonexistent config."""
        result = self.runner.invoke(app, ["generate", "nonexistent_config.yaml"])

        assert result.exit_code == 1
        assert "not found" in result.stdout

    def test_generate_invalid_config(self):
        """Test generate command with invalid config."""
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

    def test_generate_with_custom_output(self):
        """Test generate command with custom output directory."""
        # Create test configuration
        config_data = {
            "project": {"name": "Custom Output Test", "output_dir": str(self.temp_dir)},
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

        custom_output = self.temp_dir / "custom_output"

        result = self.runner.invoke(
            app, ["generate", str(config_path), "--output", str(custom_output)]
        )

        assert result.exit_code == 0
        assert custom_output.exists()

        # Should have generated a screenshot in custom directory
        output_files = list(custom_output.glob("*.png"))
        assert len(output_files) >= 1

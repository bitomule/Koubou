"""Tests for the main ScreenshotGenerator class."""

import shutil
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from koubou.config import GradientConfig, ProjectConfig, ScreenshotConfig, TextOverlay
from koubou.generator import ScreenshotGenerator


class TestScreenshotGenerator:
    """Tests for ScreenshotGenerator."""

    def setup_method(self):
        """Setup test method."""
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create test source image
        self.source_image_path = self.temp_dir / "source.png"
        source_image = Image.new("RGBA", (200, 400), (255, 0, 0, 255))  # Red
        source_image.save(self.source_image_path)

        # Create mock frame directory
        self.frame_dir = self.temp_dir / "frames"
        self.frame_dir.mkdir()

        # Create mock frame
        frame_image = Image.new("RGBA", (300, 600), (128, 128, 128, 255))
        frame_path = self.frame_dir / "Test Frame.png"
        frame_image.save(frame_path)

        # Create frame metadata
        metadata = {
            "Test Frame": {
                "screen_bounds": {"x": 50, "y": 100, "width": 200, "height": 400}
            }
        }

        import json

        with open(self.frame_dir / "Frames.json", "w") as f:
            json.dump(metadata, f)

        self.generator = ScreenshotGenerator(frame_directory=str(self.frame_dir))

    def teardown_method(self):
        """Cleanup after test."""
        shutil.rmtree(self.temp_dir)

    def test_simple_kouboueration(self):
        """Test generating a simple screenshot."""
        config = ScreenshotConfig(
            name="Simple Test",
            source_image=str(self.source_image_path),
            output_size=(400, 800),
            output_path=str(self.temp_dir / "output.png"),
        )

        result_path = self.generator.generate_screenshot(config)

        assert result_path.exists()

        # Verify output image
        output_image = Image.open(result_path)
        assert output_image.size == (400, 800)

    def test_screenshot_with_background(self):
        """Test generating screenshot with background."""
        config = ScreenshotConfig(
            name="Background Test",
            source_image=str(self.source_image_path),
            output_size=(400, 800),
            output_path=str(self.temp_dir / "output_bg.png"),
            background=GradientConfig(type="solid", colors=["#0066cc"]),
        )

        result_path = self.generator.generate_screenshot(config)

        assert result_path.exists()

        # Verify output
        output_image = Image.open(result_path)
        assert output_image.size == (400, 800)

    def test_screenshot_with_text(self):
        """Test generating screenshot with text overlay."""
        config = ScreenshotConfig(
            name="Text Test",
            source_image=str(self.source_image_path),
            output_size=(400, 800),
            output_path=str(self.temp_dir / "output_text.png"),
            text_overlays=[
                TextOverlay(
                    content="Hello World",
                    position=(50, 50),
                    font_size=32,
                    color="#ffffff",
                )
            ],
        )

        result_path = self.generator.generate_screenshot(config)

        assert result_path.exists()

        # Verify output
        output_image = Image.open(result_path)
        assert output_image.size == (400, 800)

    def test_screenshot_with_device_frame(self):
        """Test generating screenshot with device frame."""
        config = ScreenshotConfig(
            name="Frame Test",
            source_image=str(self.source_image_path),
            output_size=(300, 600),  # Match frame size
            output_path=str(self.temp_dir / "output_frame.png"),
            device_frame="Test Frame",
        )

        result_path = self.generator.generate_screenshot(config)

        assert result_path.exists()

        # Verify output
        output_image = Image.open(result_path)
        assert output_image.size == (300, 600)

    def test_complete_screenshot(self):
        """Test generating screenshot with all features."""
        config = ScreenshotConfig(
            name="Complete Test",
            source_image=str(self.source_image_path),
            output_size=(400, 800),
            output_path=str(self.temp_dir / "output_complete.png"),
            background=GradientConfig(
                type="linear", colors=["#ff0000", "#0000ff"], direction=45
            ),
            text_overlays=[
                TextOverlay(
                    content="Amazing App",
                    position=(100, 100),
                    font_size=36,
                    color="#ffffff",
                    alignment="center",
                    max_width=300,
                )
            ],
        )

        result_path = self.generator.generate_screenshot(config)

        assert result_path.exists()

        # Verify output
        output_image = Image.open(result_path)
        assert output_image.size == (400, 800)

    def test_nonexistent_source_image(self):
        """Test handling of nonexistent source image."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="Source image not found"):
            ScreenshotConfig(
                name="Invalid Test",
                source_image="/nonexistent/path.png",
                output_size=(400, 800),
            )

    def test_output_path_generation(self):
        """Test automatic output path generation."""
        config = ScreenshotConfig(
            name="Auto Path Test",
            source_image=str(self.source_image_path),
            output_size=(400, 800),
            # No output_path specified
        )

        result_path = self.generator.generate_screenshot(config)

        # Should generate a path based on name
        assert "auto_path_test" in str(result_path).lower()
        assert result_path.exists()

    def test_project_generation(self):
        """Test generating multiple screenshots as a project."""
        from koubou.config import ContentItem, ProjectInfo, ScreenshotDefinition

        project_config = ProjectConfig(
            project=ProjectInfo(
                name="Test Project", output_dir=str(self.temp_dir / "project_output")
            ),
            screenshots={
                "screenshot1": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="image",
                            asset=str(self.source_image_path),
                            position=("50%", "50%"),
                        )
                    ],
                    frame=False,  # Explicitly disable frames for this test
                ),
                "screenshot2": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="image",
                            asset=str(self.source_image_path),
                            position=("50%", "50%"),
                        ),
                        ContentItem(
                            type="text", content="Test Text", position=("50%", "20%")
                        ),
                    ],
                    frame=False,  # Explicitly disable frames for this test
                ),
            },
        )

        results = self.generator.generate_project(project_config)

        assert len(results) == 2
        for result_path in results:
            assert result_path.exists()

    def test_jpeg_output(self):
        """Test JPEG output format."""
        config = ScreenshotConfig(
            name="JPEG Test",
            source_image=str(self.source_image_path),
            output_size=(400, 800),
            output_path=str(self.temp_dir / "output.jpg"),  # JPEG extension
        )

        result_path = self.generator.generate_screenshot(config)

        assert result_path.exists()
        assert result_path.suffix == ".jpg"

        # Verify it's actually a JPEG
        output_image = Image.open(result_path)
        assert output_image.format == "JPEG"

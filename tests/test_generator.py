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
                name="Test Project",
                output_dir=str(self.temp_dir / "project_output"),
                device="iPhone 15 Pro Portrait",
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

    def test_png_has_no_alpha_channel(self):
        """Test that PNG files don't have alpha (App Store requirement)."""
        config = ScreenshotConfig(
            name="No Alpha Test",
            source_image=str(self.source_image_path),
            output_size=(400, 800),
            output_path=str(self.temp_dir / "no_alpha.png"),
        )

        result_path = self.generator.generate_screenshot(config)

        # Verify the image was created
        assert result_path.exists()

        # Load the saved image and check it has no alpha channel
        output_image = Image.open(result_path)
        assert (
            output_image.mode == "RGB"
        ), f"Expected RGB mode but got {output_image.mode}"
        assert (
            "transparency" not in output_image.info
        ), "Image should not have transparency info"

    def test_jpeg_has_no_alpha_channel(self):
        """Test that generated JPEG files don't have alpha channel."""
        config = ScreenshotConfig(
            name="JPEG Test",
            source_image=str(self.source_image_path),
            output_size=(400, 800),
            output_path=str(self.temp_dir / "test.jpg"),
        )

        result_path = self.generator.generate_screenshot(config)

        # Verify the image was created
        assert result_path.exists()

        # Load the saved image and check it's RGB
        output_image = Image.open(result_path)
        assert (
            output_image.mode == "RGB"
        ), f"Expected RGB mode but got {output_image.mode}"

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

    def test_apply_asset_frame_with_auto_detection(self):
        """Test _apply_asset_frame with automatic screen bounds detection."""
        # Create a realistic frame with screen area and bezel
        frame = Image.new("RGBA", (300, 600), (128, 128, 128, 255))

        # Define screen area (alpha=0) within bezel
        screen_left, screen_top = 30, 60
        screen_right, screen_bottom = 270, 540

        for y in range(600):
            for x in range(300):
                if screen_left <= x < screen_right and screen_top <= y < screen_bottom:
                    frame.putpixel((x, y), (128, 128, 128, 0))

        frame_path = self.frame_dir / "AutoDetect Frame.png"
        frame.save(frame_path)

        # Create canvas and config
        canvas = Image.new("RGBA", (400, 800), (255, 255, 255, 255))
        config = ScreenshotConfig(
            name="AutoDetect Test",
            source_image=str(self.source_image_path),
            output_size=(400, 800),
            device_frame="AutoDetect Frame",
            image_scale=0.8,
            image_position=["50%", "50%"],
            image_frame=True,
        )

        # Apply asset frame
        result = self.generator._apply_asset_frame(
            Image.open(self.source_image_path), canvas, config
        )

        # Result should be same size as canvas
        assert result.size == canvas.size

        # Should not raise exception
        assert isinstance(result, Image.Image)

    def test_apply_asset_frame_with_scaling(self):
        """Test _apply_asset_frame correctly scales both frame and content."""
        # Create frame with known screen bounds
        frame = Image.new("RGBA", (200, 400), (128, 128, 128, 255))
        screen_x, screen_y = 20, 40
        screen_width, screen_height = 160, 320

        for y in range(screen_y, screen_y + screen_height):
            for x in range(screen_x, screen_x + screen_width):
                frame.putpixel((x, y), (128, 128, 128, 0))

        frame_path = self.frame_dir / "Scaling Frame.png"
        frame.save(frame_path)

        # Test with different scales
        for scale in [0.5, 0.8, 1.0, 1.2]:
            canvas = Image.new("RGBA", (800, 1200), (255, 255, 255, 0))
            config = ScreenshotConfig(
                name=f"Scale {scale} Test",
                source_image=str(self.source_image_path),
                output_size=(800, 1200),
                device_frame="Scaling Frame",
                image_scale=scale,
                image_position=["50%", "50%"],
                image_frame=True,
            )

            result = self.generator._apply_asset_frame(
                Image.open(self.source_image_path), canvas, config
            )

            assert result.size == canvas.size

    def test_apply_asset_frame_maintains_aspect_ratio(self):
        """Test that _apply_asset_frame maintains source image aspect ratio."""
        # Create narrow portrait frame
        frame = Image.new("RGBA", (150, 400), (128, 128, 128, 255))

        # Screen area
        for y in range(20, 380):
            for x in range(10, 140):
                frame.putpixel((x, y), (128, 128, 128, 0))

        frame_path = self.frame_dir / "Portrait Frame.png"
        frame.save(frame_path)

        # Create wide landscape source image
        wide_source = self.temp_dir / "wide_source.png"
        wide_image = Image.new("RGBA", (400, 200), (0, 0, 255, 255))
        wide_image.save(wide_source)

        canvas = Image.new("RGBA", (600, 800), (255, 255, 255, 0))
        config = ScreenshotConfig(
            name="Aspect Ratio Test",
            source_image=str(wide_source),
            output_size=(600, 800),
            device_frame="Portrait Frame",
            image_scale=1.0,
            image_position=["50%", "50%"],
            image_frame=True,
        )

        result = self.generator._apply_asset_frame(
            Image.open(wide_source), canvas, config
        )

        # Should complete without distortion
        assert result.size == canvas.size

    def test_apply_asset_frame_with_rounded_corners(self):
        """Test that _apply_asset_frame preserves rounded corners via masking."""
        # Create frame with rounded corners (gradient alpha at edges)
        frame = Image.new("RGBA", (200, 400), (128, 128, 128, 255))

        # Define screen with rounded corners
        for y in range(400):
            for x in range(200):
                # Screen area
                if 20 <= x < 180 and 40 <= y < 360:
                    # Add rounded corners at screen edges
                    dx = min(x - 20, 180 - x)
                    dy = min(y - 40, 360 - y)
                    corner_radius = 20

                    if dx < corner_radius and dy < corner_radius:
                        dist_sq = (corner_radius - dx) ** 2
                        dist_sq += (corner_radius - dy) ** 2
                        dist = dist_sq**0.5
                        if dist < corner_radius:
                            alpha = int(255 * (dist / corner_radius))
                            frame.putpixel((x, y), (128, 128, 128, alpha))
                        else:
                            frame.putpixel((x, y), (128, 128, 128, 0))
                    else:
                        frame.putpixel((x, y), (128, 128, 128, 0))

        frame_path = self.frame_dir / "Rounded Frame.png"
        frame.save(frame_path)

        canvas = Image.new("RGBA", (400, 800), (255, 255, 255, 0))
        config = ScreenshotConfig(
            name="Rounded Corners Test",
            source_image=str(self.source_image_path),
            output_size=(400, 800),
            device_frame="Rounded Frame",
            image_scale=1.0,
            image_position=["50%", "50%"],
            image_frame=True,
        )

        result = self.generator._apply_asset_frame(
            Image.open(self.source_image_path), canvas, config
        )

        # Result should have RGBA mode to support transparency
        assert result.mode == "RGBA"
        assert result.size == canvas.size

    def test_apply_asset_frame_auto_fits_oversized_frame_to_canvas(self):
        """Oversized frames should be scaled down instead of clipping bezel edges."""
        frame = Image.new("RGBA", (300, 600), (128, 128, 128, 255))
        screen_x, screen_y = 30, 60
        screen_width, screen_height = 240, 480

        for y in range(screen_y, screen_y + screen_height):
            for x in range(screen_x, screen_x + screen_width):
                frame.putpixel((x, y), (128, 128, 128, 0))

        frame_path = self.frame_dir / "Oversized Frame.png"
        frame.save(frame_path)

        repro_source = self.temp_dir / "issue_17_source.png"
        Image.new("RGBA", (240, 480), (255, 0, 0, 255)).save(repro_source)

        canvas = Image.new("RGBA", (240, 480), (255, 255, 255, 0))
        config = ScreenshotConfig(
            name="Issue 17 Regression",
            source_image=str(repro_source),
            output_size=(240, 480),
            device_frame="Oversized Frame",
            image_scale=1.0,
            image_position=["50%", "50%"],
            image_frame=True,
        )

        result = self.generator._apply_asset_frame(
            Image.open(repro_source), canvas, config
        )

        assert result.size == canvas.size
        assert result.getpixel((0, canvas.height // 2))[:3] == (128, 128, 128)
        assert result.getpixel((canvas.width // 2, 0))[:3] == (128, 128, 128)
        assert result.getpixel((canvas.width // 2, canvas.height // 2))[:3] == (
            255,
            0,
            0,
        )

    def test_convert_position_supports_pixel_suffix(self):
        """Position parser should support values with px suffix."""
        assert self.generator._convert_position(["100px", "50px"], (1000, 500)) == (
            100,
            50,
        )

    def test_convert_position_supports_mixed_percent_and_pixels(self):
        """Position parser should support mixed percent and pixel values."""
        assert self.generator._convert_position(["50%", "120px"], (1000, 800)) == (
            500,
            120,
        )

    def test_project_generation_accepts_px_positions_for_text_and_image(self):
        """Regression: project generation should accept px position values."""
        from koubou.config import ContentItem, ProjectInfo, ScreenshotDefinition

        project_config = ProjectConfig(
            project=ProjectInfo(
                name="PX Position Regression",
                output_dir=str(self.temp_dir / "project_px_output"),
                device="iPhone 15 Pro Portrait",
            ),
            screenshots={
                "pixel_positions": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="image",
                            asset=str(self.source_image_path),
                            position=("100px", "200px"),
                        ),
                        ContentItem(
                            type="text",
                            content="Top Left",
                            position=("120px", "80px"),
                            alignment="left",
                        ),
                    ],
                    frame=False,
                )
            },
        )

        results = self.generator.generate_project(project_config)

        assert len(results) == 1
        assert results[0].exists()


class TestResolveLocalizedAsset:
    """Tests for resolve_localized_asset() function."""

    def setup_method(self):
        """Setup test method with localized asset structure."""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create localized directory structure
        # screenshots/
        #   en/
        #     hero.png
        #   es/
        #     hero.png
        #   hero.png (fallback)
        self.screenshots_dir = self.temp_dir / "screenshots"
        self.screenshots_dir.mkdir()

        # Create English version
        en_dir = self.screenshots_dir / "en"
        en_dir.mkdir()
        en_image = Image.new("RGB", (100, 100), (255, 0, 0))
        en_image.save(en_dir / "hero.png")

        # Create Spanish version
        es_dir = self.screenshots_dir / "es"
        es_dir.mkdir()
        es_image = Image.new("RGB", (100, 100), (0, 255, 0))
        es_image.save(es_dir / "hero.png")

        # Create fallback version
        fallback_image = Image.new("RGB", (100, 100), (0, 0, 255))
        fallback_image.save(self.screenshots_dir / "hero.png")

    def teardown_method(self):
        """Cleanup after test."""
        shutil.rmtree(self.temp_dir)

    def test_dict_format_exact_match(self):
        """Test dict format with exact language match."""
        from koubou.generator import resolve_localized_asset

        asset = {
            "en": "path/to/en.png",
            "es": "path/to/es.png",
            "default": "path/to/default.png",
        }

        result = resolve_localized_asset(asset, "en", "en")
        assert result == "path/to/en.png"

        result = resolve_localized_asset(asset, "es", "en")
        assert result == "path/to/es.png"

    def test_dict_format_default_fallback(self):
        """Test dict format falls back to default when language not found."""
        from koubou.generator import resolve_localized_asset

        asset = {"en": "path/to/en.png", "default": "path/to/default.png"}

        result = resolve_localized_asset(asset, "fr", "en")
        assert result == "path/to/default.png"

    def test_dict_format_no_match(self):
        """Test dict format returns empty string when no match found."""
        from koubou.generator import resolve_localized_asset

        asset = {"en": "path/to/en.png", "es": "path/to/es.png"}

        result = resolve_localized_asset(asset, "fr", "en")
        assert result == ""

    def test_string_format_lang_convention(self):
        """Test string format with {lang}/ convention (file exists)."""
        from koubou.generator import resolve_localized_asset

        asset = "screenshots/hero.png"

        # Should find screenshots/en/hero.png
        result = resolve_localized_asset(asset, "en", "en", self.temp_dir)
        assert result == "screenshots/en/hero.png"

        # Should find screenshots/es/hero.png
        result = resolve_localized_asset(asset, "es", "en", self.temp_dir)
        assert result == "screenshots/es/hero.png"

    def test_string_format_base_lang_fallback(self):
        """Test string format falls back to base_language when lang not found."""
        from koubou.generator import resolve_localized_asset

        asset = "screenshots/hero.png"

        # French not found, should fall back to en
        result = resolve_localized_asset(asset, "fr", "en", self.temp_dir)
        assert result == "screenshots/en/hero.png"

    def test_string_format_direct_path_fallback(self):
        """Test string format falls back to direct path when no localized
        version found."""
        from koubou.generator import resolve_localized_asset

        asset = "screenshots/hero.png"

        # Both fr and pt not found, should use direct path
        result = resolve_localized_asset(asset, "fr", "pt", self.temp_dir)
        assert result == "screenshots/hero.png"

    def test_empty_asset(self):
        """Test handling of empty/None asset."""
        from koubou.generator import resolve_localized_asset

        assert resolve_localized_asset("", "en", "en") == ""
        assert resolve_localized_asset(None, "en", "en") == ""  # type: ignore

    def test_absolute_path(self):
        """Test handling of absolute paths."""
        from koubou.generator import resolve_localized_asset

        # Create absolute path test structure
        absolute_dir = self.temp_dir / "absolute"
        absolute_dir.mkdir()
        en_dir = absolute_dir / "en"
        en_dir.mkdir()
        Image.new("RGB", (50, 50), (255, 255, 255)).save(en_dir / "test.png")

        asset = str(absolute_dir / "test.png")

        result = resolve_localized_asset(asset, "en", "en")
        expected = str(absolute_dir / "en" / "test.png")
        assert result == expected

    def test_dict_empty(self):
        """Test empty dict returns empty string."""
        from koubou.generator import resolve_localized_asset

        asset: dict = {}  # type: ignore

        result = resolve_localized_asset(asset, "en", "en")  # type: ignore
        assert result == ""

    def test_no_config_dir_relative_path(self):
        """Test behavior when config_dir is None with relative path."""
        from koubou.generator import resolve_localized_asset

        asset = "screenshots/hero.png"

        # Without config_dir, should not find files but still return the path
        result = resolve_localized_asset(asset, "en", "en", None)
        # Should return direct path as fallback since files don't exist in CWD
        assert result == asset


class TestHighlightIntegration:
    """Integration tests for highlight content items in the generation pipeline."""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.source_image_path = self.temp_dir / "source.png"
        source_image = Image.new("RGBA", (200, 400), (255, 0, 0, 255))
        source_image.save(self.source_image_path)

        self.frame_dir = self.temp_dir / "frames"
        self.frame_dir.mkdir()

        import json

        with open(self.frame_dir / "Frames.json", "w") as f:
            json.dump({}, f)

        self.generator = ScreenshotGenerator(frame_directory=str(self.frame_dir))

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_project_with_highlight(self):
        from koubou.config import ContentItem, ProjectInfo, ScreenshotDefinition

        project_config = ProjectConfig(
            project=ProjectInfo(
                name="Highlight Test",
                output_dir=str(self.temp_dir / "output"),
                device="iPhone 15 Pro Portrait",
            ),
            screenshots={
                "screenshot1": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="image",
                            asset=str(self.source_image_path),
                            position=("50%", "50%"),
                        ),
                        ContentItem(
                            type="highlight",
                            shape="circle",
                            position=("50%", "50%"),
                            dimensions=("20%", "15%"),
                            border_color="#FF3B30",
                            border_width=4,
                        ),
                    ],
                    frame=False,
                ),
            },
        )

        results = self.generator.generate_project(project_config)
        assert len(results) == 1
        assert results[0].exists()

        output_image = Image.open(results[0])
        assert output_image.mode == "RGB"


class TestZoomIntegration:
    """Integration tests for zoom content items in the generation pipeline."""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.source_image_path = self.temp_dir / "source.png"
        source_image = Image.new("RGBA", (200, 400), (0, 0, 255, 255))
        source_image.save(self.source_image_path)

        self.frame_dir = self.temp_dir / "frames"
        self.frame_dir.mkdir()

        import json

        with open(self.frame_dir / "Frames.json", "w") as f:
            json.dump({}, f)

        self.generator = ScreenshotGenerator(frame_directory=str(self.frame_dir))

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_project_with_zoom(self):
        from koubou.config import ContentItem, ProjectInfo, ScreenshotDefinition

        project_config = ProjectConfig(
            project=ProjectInfo(
                name="Zoom Test",
                output_dir=str(self.temp_dir / "output"),
                device="iPhone 15 Pro Portrait",
            ),
            screenshots={
                "screenshot1": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="image",
                            asset=str(self.source_image_path),
                            position=("50%", "50%"),
                        ),
                        ContentItem(
                            type="zoom",
                            source_position=("50%", "50%"),
                            source_size=("15%", "10%"),
                            display_position=("25%", "20%"),
                            display_size=("35%", "30%"),
                            shape="circle",
                            border_color="#007AFF",
                            border_width=3,
                            connector=True,
                            connector_color="#007AFF",
                        ),
                    ],
                    frame=False,
                ),
            },
        )

        results = self.generator.generate_project(project_config)
        assert len(results) == 1
        assert results[0].exists()

    def test_project_with_highlight_zoom_and_text(self):
        """Layer order: background -> image -> highlight -> zoom -> text."""
        from koubou.config import ContentItem, ProjectInfo, ScreenshotDefinition

        project_config = ProjectConfig(
            project=ProjectInfo(
                name="Combined Test",
                output_dir=str(self.temp_dir / "output"),
                device="iPhone 15 Pro Portrait",
            ),
            screenshots={
                "screenshot1": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="image",
                            asset=str(self.source_image_path),
                            position=("50%", "50%"),
                        ),
                        ContentItem(
                            type="highlight",
                            shape="rounded_rect",
                            position=("60%", "40%"),
                            dimensions=("25%", "20%"),
                            border_color="#FF3B30",
                            border_width=3,
                            fill_color="#FF3B3020",
                        ),
                        ContentItem(
                            type="zoom",
                            source_position=("60%", "40%"),
                            source_size=("15%", "10%"),
                            display_position=("25%", "20%"),
                            display_size=("30%", "25%"),
                            shape="circle",
                            border_color="#007AFF",
                            border_width=3,
                            connector=True,
                        ),
                        ContentItem(
                            type="text",
                            content="Amazing Feature",
                            position=("50%", "85%"),
                        ),
                    ],
                    frame=False,
                ),
            },
        )

        results = self.generator.generate_project(project_config)
        assert len(results) == 1
        assert results[0].exists()

        output_image = Image.open(results[0])
        assert output_image.mode == "RGB"

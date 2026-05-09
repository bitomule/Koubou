"""Tests for HTML template rendering."""

import importlib
import io
import json
import shutil
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from koubou.config import (
    ContentItem,
    ProjectConfig,
    ProjectInfo,
    ScreenshotDefinition,
)


def _playwright_available():
    return importlib.util.find_spec("playwright") is not None


def _html_runtime_available():
    if not _playwright_available():
        return False

    from koubou.html_setup import check_html_environment

    return check_html_environment().ready


requires_playwright = pytest.mark.skipif(
    not _html_runtime_available(),
    reason="HTML rendering runtime not available in test environment",
)


@pytest.fixture
def temp_dir():
    d = Path(tempfile.mkdtemp())
    yield d
    shutil.rmtree(d)


@pytest.fixture
def renderer():
    from koubou.renderers.html_renderer import HtmlRenderer

    r = HtmlRenderer()
    yield r
    r.close()


class TestScreenshotDefinitionValidation:
    """Test template/content mutual exclusion in config."""

    def test_template_and_content_mutually_exclusive(self):
        with pytest.raises(Exception, match="Cannot specify both"):
            ScreenshotDefinition(
                content=[],
                template="some.html",
            )

    def test_requires_template_or_content(self):
        with pytest.raises(Exception, match="Must specify either"):
            ScreenshotDefinition()

    def test_template_only_is_valid(self):
        defn = ScreenshotDefinition(
            template="hero.html",
            variables={"headline": "Hello"},
        )
        assert defn.template == "hero.html"
        assert defn.variables == {"headline": "Hello"}
        assert defn.content is None

    def test_content_only_is_valid(self):
        defn = ScreenshotDefinition(
            content=[
                ContentItem(
                    type="text",
                    content="Hello",
                    position=("50%", "50%"),
                )
            ],
        )
        assert defn.content is not None
        assert defn.template is None


class TestLayoutManifestHelpers:
    """Unit tests for compact layout JSON helpers."""

    def test_build_layout_manifest_with_overlap(self):
        from koubou.renderers.html_renderer import _build_layout_manifest

        manifest = _build_layout_manifest(
            [
                {
                    "id": "headline",
                    "role": "headline",
                    "text": "Track every expense",
                    "left": 40,
                    "top": 80,
                    "right": 360,
                    "bottom": 240,
                },
                {
                    "id": "phone",
                    "role": "device",
                    "src": "app_screenshot.png",
                    "left": 200,
                    "top": 180,
                    "right": 520,
                    "bottom": 700,
                    "zIndex": 2,
                },
            ],
            (800, 1000),
        )

        assert manifest == {
            "version": 1,
            "elements": [
                {
                    "id": "headline",
                    "role": "headline",
                    "text": "Track every expense",
                    "x": 0.05,
                    "y": 0.08,
                    "width": 0.4,
                    "height": 0.16,
                },
                {
                    "id": "phone",
                    "role": "device",
                    "src": "app_screenshot.png",
                    "x": 0.25,
                    "y": 0.18,
                    "width": 0.4,
                    "height": 0.52,
                    "zIndex": 2,
                },
            ],
            "overlaps": [
                {
                    "first": "headline",
                    "second": "phone",
                    "x": 0.25,
                    "y": 0.18,
                    "width": 0.2,
                    "height": 0.06,
                }
            ],
        }

    def test_build_layout_manifest_clips_to_canvas(self):
        from koubou.renderers.html_renderer import _build_layout_manifest

        manifest = _build_layout_manifest(
            [
                {
                    "id": "offscreen",
                    "left": -40,
                    "top": -20,
                    "right": 120,
                    "bottom": 80,
                }
            ],
            (200, 100),
        )

        assert manifest == {
            "version": 1,
            "elements": [
                {
                    "id": "offscreen",
                    "x": 0.0,
                    "y": 0.0,
                    "width": 0.6,
                    "height": 0.8,
                }
            ],
            "overlaps": [],
        }


@requires_playwright
class TestHtmlRenderer:
    """Integration tests for HTML rendering (requires playwright)."""

    def test_basic_html_rendering(self, temp_dir, renderer):
        template = temp_dir / "test.html"
        template.write_text(
            """<!DOCTYPE html>
<html>
<body style="margin:0; background: linear-gradient(135deg, #667eea, #764ba2);
             width:100vw; height:100vh;">
  <h1 style="color:white; text-align:center; padding-top:40%;">
    {{headline}}
  </h1>
</body>
</html>"""
        )

        png_bytes = renderer.render(
            template_path=template,
            variables={"headline": "Privacy First"},
            size=(1320, 2868),
        )

        assert len(png_bytes) > 0
        img = Image.open(io.BytesIO(png_bytes))
        assert img.size == (1320, 2868)

    def test_variable_substitution(self, temp_dir, renderer):
        template = temp_dir / "vars.html"
        template.write_text(
            """<!DOCTYPE html>
<html>
<body style="margin:0; width:100vw; height:100vh; background:#fff;">
  <p id="title">{{title}}</p>
  <p id="sub">{{subtitle}}</p>
</body>
</html>"""
        )

        png_bytes = renderer.render(
            template_path=template,
            variables={"title": "Hello", "subtitle": "World"},
            size=(400, 800),
        )
        assert len(png_bytes) > 0

    def test_asset_symlink_in_sandbox(self, temp_dir, renderer):
        asset_path = temp_dir / "real_asset.png"
        img = Image.new("RGB", (100, 100), (255, 0, 0))
        img.save(asset_path)

        template = temp_dir / "asset.html"
        template.write_text(
            """<!DOCTYPE html>
<html>
<body style="margin:0; width:100vw; height:100vh; background:#000;">
  <img src="screen.png" style="width:50px; height:50px;">
</body>
</html>"""
        )

        png_bytes = renderer.render(
            template_path=template,
            variables={},
            size=(400, 800),
            assets={"screen.png": str(asset_path)},
        )
        assert len(png_bytes) > 0

    def test_sibling_files_mounted_in_sandbox(self, temp_dir, renderer):
        """Template sibling files (CSS, images) should resolve in the sandbox."""
        # Create template directory with siblings
        tpl_dir = temp_dir / "templates"
        tpl_dir.mkdir()

        (tpl_dir / "styles.css").write_text("body { background: red; margin: 0; }")

        logo = Image.new("RGB", (50, 50), (0, 255, 0))
        logo.save(tpl_dir / "logo.png")

        template = tpl_dir / "hero.html"
        template.write_text(
            """<!DOCTYPE html>
<html>
<head><link rel="stylesheet" href="styles.css"></head>
<body style="width:100vw; height:100vh;">
  <img src="logo.png" style="width:50px; height:50px;">
</body>
</html>"""
        )

        png_bytes = renderer.render(
            template_path=template,
            variables={},
            size=(400, 800),
        )
        assert len(png_bytes) > 0
        img = Image.open(io.BytesIO(png_bytes))
        assert img.size == (400, 800)

    def test_project_generate_with_template(self, temp_dir):
        """End-to-end: generate a project with an HTML template screenshot."""
        from koubou.generator import ScreenshotGenerator

        template = temp_dir / "hero.html"
        template.write_text(
            """<!DOCTYPE html>
<html>
<body style="margin:0; background:#1a1a2e; width:100vw; height:100vh;">
  <h1 data-kou-id="headline" data-kou-role="headline"
      style="color:white; text-align:center; padding-top:40%;">
    {{headline}}
  </h1>
</body>
</html>"""
        )

        output_dir = temp_dir / "output"

        config = ProjectConfig(
            project=ProjectInfo(
                name="TestHTML",
                output_dir=str(output_dir),
                device="iPhone 16 Pro - Black Titanium - Portrait",
                output_size="iPhone6_9",
            ),
            screenshots={
                "hero": ScreenshotDefinition(
                    template=str(template),
                    variables={"headline": "Privacy First"},
                ),
            },
        )

        generator = ScreenshotGenerator()
        results = generator.generate_project(config, config_dir=temp_dir)

        assert len(results) == 1
        assert results[0].exists()
        assert results[0].with_suffix(".layout.json").exists()

        img = Image.open(results[0])
        assert img.size == (1320, 2868)

        layout = json.loads(results[0].with_suffix(".layout.json").read_text())
        assert layout["version"] == 1
        assert len(layout["elements"]) == 1
        assert layout["elements"][0]["id"] == "headline"
        assert layout["elements"][0]["role"] == "headline"
        assert layout["overlaps"] == []

    def test_project_generate_with_template_custom_font_asset(
        self, temp_dir, system_font_file
    ):
        """End-to-end: HTML templates should load custom fonts via assets."""
        from koubou.generator import ScreenshotGenerator

        font_dir = temp_dir / "assets" / "fonts"
        font_dir.mkdir(parents=True)
        font_path = font_dir / "BrandFont.ttf"
        shutil.copyfile(system_font_file, font_path)

        template = temp_dir / "hero.html"
        template.write_text(
            """<!DOCTYPE html>
<html>
<head>
  <style>
    @font-face {
      font-family: "Brand Display";
      src: url("{{brand_font}}") format("truetype");
      font-weight: 700;
    }
    body {
      margin: 0;
      background: #111827;
      width: 100vw;
      height: 100vh;
      display: grid;
      place-items: center;
    }
    h1 {
      color: white;
      font-family: "Brand Display", sans-serif;
      font-size: 64px;
    }
  </style>
</head>
<body>
  <h1 data-kou-id="headline" data-kou-role="headline">Custom Font</h1>
</body>
</html>""",
            encoding="utf-8",
        )

        output_dir = temp_dir / "output"
        config = ProjectConfig(
            project=ProjectInfo(
                name="TestHTMLFont",
                output_dir=str(output_dir),
                device="iPhone 16 Pro - Black Titanium - Portrait",
                output_size=[400, 800],
            ),
            screenshots={
                "hero": ScreenshotDefinition(
                    template="hero.html",
                    assets={"brand_font": "assets/fonts/BrandFont.ttf"},
                    frame=False,
                ),
            },
        )

        generator = ScreenshotGenerator()
        results = generator.generate_project(config, config_dir=temp_dir)

        assert len(results) == 1
        assert results[0].exists()

        img = Image.open(results[0])
        assert img.size == (400, 800)

        layout = json.loads(results[0].with_suffix(".layout.json").read_text())
        assert layout["elements"][0]["id"] == "headline"

    def test_render_staged_with_layout_returns_empty_manifest_without_annotations(
        self, temp_dir, renderer
    ):
        template = temp_dir / "plain.html"
        template.write_text(
            """<!DOCTYPE html>
<html>
<body style="margin:0; width:100vw; height:100vh; background:#fff;">
  <p>Hello</p>
</body>
</html>"""
        )

        result = renderer.render_with_layout(
            template_path=template,
            variables={},
            size=(400, 800),
        )

        assert len(result.png_bytes) > 0
        assert result.layout == {"version": 1, "elements": [], "overlaps": []}


class TestDependencyAnalyzerHtml:
    """Test that dependency analyzer tracks HTML templates."""

    def test_tracks_template_file(self, temp_dir):
        from koubou.dependency_analyzer import DependencyAnalyzer

        template = temp_dir / "hero.html"
        template.write_text("<html><body>Hello</body></html>")

        config = ProjectConfig(
            project=ProjectInfo(
                name="Test",
                output_dir=str(temp_dir / "output"),
                device="iPhone 16 Pro - Black Titanium - Portrait",
            ),
            screenshots={
                "hero": ScreenshotDefinition(
                    template=str(template),
                ),
            },
        )

        analyzer = DependencyAnalyzer()
        analyzer.analyze_project(config, temp_dir)

        asset_paths = analyzer.get_all_asset_paths()
        resolved_template = template.resolve()
        assert resolved_template in asset_paths

        affected = analyzer.get_asset_screenshots(resolved_template)
        assert "hero" in affected

    def test_tracks_sibling_files(self, temp_dir):
        from koubou.dependency_analyzer import DependencyAnalyzer

        tpl_dir = temp_dir / "templates"
        tpl_dir.mkdir()

        template = tpl_dir / "hero.html"
        template.write_text("<html><body>Hello</body></html>")

        css_file = tpl_dir / "styles.css"
        css_file.write_text("body { color: red; }")

        config = ProjectConfig(
            project=ProjectInfo(
                name="Test",
                output_dir=str(temp_dir / "output"),
                device="iPhone 16 Pro - Black Titanium - Portrait",
            ),
            screenshots={
                "hero": ScreenshotDefinition(
                    template=str(template),
                ),
            },
        )

        analyzer = DependencyAnalyzer()
        analyzer.analyze_project(config, temp_dir)

        affected = analyzer.get_asset_screenshots(css_file)
        assert "hero" in affected

    def test_tracks_nested_template_assets(self, temp_dir):
        from koubou.dependency_analyzer import DependencyAnalyzer

        tpl_dir = temp_dir / "templates"
        nested_dir = tpl_dir / "assets" / "icons"
        nested_dir.mkdir(parents=True)

        template = tpl_dir / "hero.html"
        template.write_text("<html><body>Hello</body></html>")

        nested_file = nested_dir / "check.svg"
        nested_file.write_text("<svg></svg>")

        config = ProjectConfig(
            project=ProjectInfo(
                name="Test",
                output_dir=str(temp_dir / "output"),
                device="iPhone 16 Pro - Black Titanium - Portrait",
            ),
            screenshots={
                "hero": ScreenshotDefinition(
                    template=str(template),
                ),
            },
        )

        analyzer = DependencyAnalyzer()
        analyzer.analyze_project(config, temp_dir)

        affected = analyzer.get_asset_screenshots(nested_file)
        assert "hero" in affected


class TestAssetsFieldValidation:
    """Test explicit variables/assets separation in ScreenshotDefinition."""

    def test_template_with_assets_and_variables(self):
        defn = ScreenshotDefinition(
            template="hero.html",
            variables={"headline": "Privacy First"},
            assets={"app_screenshot": "assets/screen1.png"},
        )
        assert defn.variables == {"headline": "Privacy First"}
        assert defn.assets == {"app_screenshot": "assets/screen1.png"}

    def test_assets_default_empty(self):
        defn = ScreenshotDefinition(
            template="hero.html",
            variables={"headline": "Hello"},
        )
        assert defn.assets == {}

    def test_variables_default_empty(self):
        defn = ScreenshotDefinition(
            template="hero.html",
            assets={"screen": "assets/screen.png"},
        )
        assert defn.variables == {}

    def test_assets_support_localized_mapping(self):
        defn = ScreenshotDefinition(
            template="hero.html",
            assets={
                "app_screenshot": {
                    "en": "assets/en/screen.png",
                    "es": "assets/es/screen.png",
                    "default": "assets/default.png",
                }
            },
        )
        assert defn.assets["app_screenshot"]["es"] == "assets/es/screen.png"


class TestHtmlTemplateAssetLocalization:
    """Test localized asset resolution for template-based screenshots."""

    def _make_generator(self, temp_dir):
        from koubou.generator import ScreenshotGenerator

        frames_dir = temp_dir / "frames"
        frames_dir.mkdir()
        (frames_dir / "Frames.json").write_text("{}", encoding="utf-8")
        (frames_dir / "Sizes.json").write_text("{}", encoding="utf-8")
        return ScreenshotGenerator(frame_directory=str(frames_dir))

    def test_prepare_html_screenshot_localizes_string_assets(self, temp_dir):
        generator = self._make_generator(temp_dir)

        template = temp_dir / "hero.html"
        template.write_text(
            '<html><body><img src="{{app_screenshot}}"></body></html>',
            encoding="utf-8",
        )

        raw_dir = temp_dir / "raw"
        (raw_dir / "en").mkdir(parents=True)
        (raw_dir / "es").mkdir(parents=True)
        Image.new("RGB", (20, 20), (255, 0, 0)).save(raw_dir / "en" / "hello.png")
        Image.new("RGB", (20, 20), (0, 255, 0)).save(raw_dir / "es" / "hello.png")

        screenshot = ScreenshotDefinition(
            template=str(template),
            assets={"app_screenshot": "raw/hello.png"},
            frame=False,
        )

        prepared = generator.prepare_html_screenshot(
            screenshot,
            temp_dir,
            language="es",
            base_language="en",
        )

        assert prepared.variables["app_screenshot"] == "app_screenshot.png"
        assert prepared.assets["app_screenshot.png"] == str(
            (raw_dir / "es" / "hello.png").resolve()
        )

    def test_prepare_html_screenshot_localizes_dict_assets(self, temp_dir):
        generator = self._make_generator(temp_dir)

        template = temp_dir / "hero.html"
        template.write_text(
            '<html><body><img src="{{app_screenshot}}"></body></html>',
            encoding="utf-8",
        )

        raw_dir = temp_dir / "raw"
        raw_dir.mkdir()
        Image.new("RGB", (20, 20), (255, 0, 0)).save(raw_dir / "fallback.png")
        Image.new("RGB", (20, 20), (0, 255, 0)).save(raw_dir / "es.png")

        screenshot = ScreenshotDefinition(
            template=str(template),
            assets={
                "app_screenshot": {
                    "es": "raw/es.png",
                    "default": "raw/fallback.png",
                }
            },
            frame=False,
        )

        prepared = generator.prepare_html_screenshot(
            screenshot,
            temp_dir,
            language="fr",
            base_language="en",
        )

        assert prepared.variables["app_screenshot"] == "app_screenshot.png"
        assert prepared.assets["app_screenshot.png"] == str(
            (raw_dir / "fallback.png").resolve()
        )

    def test_prepare_html_screenshot_exposes_font_asset_to_template(
        self, temp_dir, system_font_file
    ):
        from koubou.renderers.html_staging import stage_html_workspace

        generator = self._make_generator(temp_dir)

        font_dir = temp_dir / "assets" / "fonts"
        font_dir.mkdir(parents=True)
        font_path = font_dir / "BrandFont.ttf"
        shutil.copyfile(system_font_file, font_path)

        template = temp_dir / "hero.html"
        template.write_text(
            """<html><head><style>
@font-face {
  font-family: "Brand Display";
  src: url("{{brand_font}}") format("truetype");
}
</style></head><body>Font asset</body></html>""",
            encoding="utf-8",
        )

        screenshot = ScreenshotDefinition(
            template="hero.html",
            assets={"brand_font": "assets/fonts/BrandFont.ttf"},
            frame=False,
        )

        prepared = generator.prepare_html_screenshot(screenshot, temp_dir)

        assert prepared.variables["brand_font"] == "brand_font.ttf"
        assert prepared.assets["brand_font.ttf"] == str(font_path.resolve())

        workspace_dir = temp_dir / "workspace"
        staged_index = stage_html_workspace(
            template_path=prepared.template_path,
            variables=prepared.variables,
            destination_dir=workspace_dir,
            assets=prepared.assets,
        )

        assert (workspace_dir / "brand_font.ttf").exists()
        assert 'url("brand_font.ttf")' in staged_index.read_text(encoding="utf-8")

"""Tests for HTML template rendering."""

import importlib
import io
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


requires_playwright = pytest.mark.skipif(
    not _playwright_available(),
    reason="playwright not installed (install with: pip install koubou[html])",
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


@requires_playwright
class TestHtmlRenderer:
    """Integration tests for HTML rendering (requires playwright)."""

    def test_basic_html_rendering(self, temp_dir, renderer):
        template = temp_dir / "test.html"
        template.write_text("""<!DOCTYPE html>
<html>
<body style="margin:0; background: linear-gradient(135deg, #667eea, #764ba2);
             width:100vw; height:100vh;">
  <h1 style="color:white; text-align:center; padding-top:40%;">
    {{headline}}
  </h1>
</body>
</html>""")

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
        template.write_text("""<!DOCTYPE html>
<html>
<body style="margin:0; width:100vw; height:100vh; background:#fff;">
  <p id="title">{{title}}</p>
  <p id="sub">{{subtitle}}</p>
</body>
</html>""")

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
        template.write_text("""<!DOCTYPE html>
<html>
<body style="margin:0; width:100vw; height:100vh; background:#000;">
  <img src="screen.png" style="width:50px; height:50px;">
</body>
</html>""")

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
        template.write_text("""<!DOCTYPE html>
<html>
<head><link rel="stylesheet" href="styles.css"></head>
<body style="width:100vw; height:100vh;">
  <img src="logo.png" style="width:50px; height:50px;">
</body>
</html>""")

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
        template.write_text("""<!DOCTYPE html>
<html>
<body style="margin:0; background:#1a1a2e; width:100vw; height:100vh;">
  <h1 style="color:white; text-align:center; padding-top:40%;">
    {{headline}}
  </h1>
</body>
</html>""")

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

        img = Image.open(results[0])
        assert img.size == (1320, 2868)


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

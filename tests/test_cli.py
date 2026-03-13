"""Tests for CLI functionality."""

import importlib
import json
import tempfile
from pathlib import Path

import pytest
import yaml
from PIL import Image
from typer.testing import CliRunner

from koubou.cli import app


def _playwright_available():
    return importlib.util.find_spec("playwright") is not None


def _html_runtime_available():
    if not _playwright_available():
        return False

    from koubou.html_setup import check_html_environment

    return check_html_environment().ready


requires_html_runtime = pytest.mark.skipif(
    not _html_runtime_available(),
    reason="HTML rendering runtime not available in test environment",
)


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
        assert (
            config["project"]["device"] == "iPhone 16 Pro - Black Titanium - Portrait"
        )
        assert config["project"]["output_size"] == "iPhone6_9"
        assert "screenshots" in config
        assert (
            len(config["screenshots"]) == 3
        )  # Updated CLI generates 3 sample screenshots
        assert (self.temp_dir / "screenshots" / "home.png").exists()
        assert (self.temp_dir / "screenshots" / "features.png").exists()
        assert (self.temp_dir / "screenshots" / "gradient_demo.png").exists()

    def test_create_config_sample_generates_successfully(self):
        """Sample config should generate successfully without manual asset setup."""
        config_path = self.temp_dir / "sample_config.yaml"

        create_result = self.runner.invoke(
            app, ["--create-config", str(config_path), "--name", "Sample Project"]
        )
        assert create_result.exit_code == 0

        generate_result = self.runner.invoke(app, ["generate", str(config_path)])

        assert generate_result.exit_code == 0
        output_files = list(
            (self.temp_dir / "Screenshots" / "Generated").glob("**/*.png")
        )
        assert len(output_files) == 3

    def test_create_config_html_mode_creates_templates(self):
        """HTML mode should scaffold templates and template-based YAML."""
        config_path = self.temp_dir / "sample_html_config.yaml"

        result = self.runner.invoke(
            app,
            [
                "--create-config",
                str(config_path),
                "--mode",
                "html",
                "--name",
                "HTML Sample Project",
            ],
        )

        assert result.exit_code == 0
        assert config_path.exists()
        assert (self.temp_dir / "templates" / "hero.html").exists()
        assert (self.temp_dir / "templates" / "feature.html").exists()
        assert (self.temp_dir / "templates" / "closing.html").exists()
        assert (self.temp_dir / "templates" / "styles.css").exists()

        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert (
            config["project"]["device"] == "iPhone 16 Pro - Black Titanium - Portrait"
        )
        assert config["screenshots"]["hero"]["template"] == "templates/hero.html"
        assert (
            config["screenshots"]["hero"]["assets"]["screen"] == "screenshots/home.png"
        )

    @requires_html_runtime
    def test_create_config_html_mode_generates_successfully(self):
        """HTML sample config should render successfully with setup-html."""
        config_path = self.temp_dir / "sample_html_config.yaml"

        create_result = self.runner.invoke(
            app,
            [
                "--create-config",
                str(config_path),
                "--mode",
                "html",
                "--name",
                "HTML Sample Project",
            ],
        )
        assert create_result.exit_code == 0

        generate_result = self.runner.invoke(
            app, ["generate", str(config_path), "--setup-html"]
        )

        assert generate_result.exit_code == 0
        output_files = list(
            (self.temp_dir / "Screenshots" / "Generated").glob("**/*.png")
        )
        assert len(output_files) == 3

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
                "device": "iPhone 15 - Black - Portrait",
                "output_size": "iPhone6_9",
            },
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

        # Should have generated a screenshot in device subdirectory
        output_files = list(output_dir.glob("**/*.png"))
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
                "device": "iPhone 15 - Black - Portrait",
            },
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
        # with device subdirectory
        output_files = list(yaml_output.glob("**/*.png"))
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

    def test_inspect_frame_json_output(self):
        """Test inspect-frame JSON output."""
        result = self.runner.invoke(
            app,
            [
                "inspect-frame",
                "iPhone 16 Pro - Black Titanium - Portrait",
                "--output-size",
                "iPhone6_9",
                "--output",
                "json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["device"] == "iPhone 16 Pro - Black Titanium - Portrait"
        assert payload["output_size"] == {"width": 1320, "height": 2868}
        assert payload["canvas_class"] == "tall_iphone_portrait"
        assert payload["orientation"] == "portrait"
        assert "frame_size" in payload
        assert "screen_bounds" in payload
        assert "screen_bbox" in payload
        assert "safe_margins" in payload
        assert payload["screen_coverage_ratio"] > 0

    def test_inspect_frame_custom_output_size(self):
        """Test inspect-frame with custom output size parsing."""
        result = self.runner.invoke(
            app,
            [
                "inspect-frame",
                "iPhone 16 Pro - Black Titanium - Portrait",
                "--output-size",
                "1200x2600",
                "--output",
                "json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["output_size"] == {"width": 1200, "height": 2600}
        assert payload["canvas_class"] == "tall_iphone_portrait"

    def test_setup_html_help(self):
        """Test setup-html help output."""
        result = self.runner.invoke(app, ["setup-html", "--help"])

        assert result.exit_code == 0
        assert "Prepare HTML rendering support" in result.stdout

    def test_generate_with_setup_html(self, monkeypatch):
        """Test generate --setup-html prepares HTML before generation."""
        template_path = self.temp_dir / "hero.html"
        template_path.write_text("<html><body>{{headline}}</body></html>")

        config_data = {
            "project": {
                "name": "HTML CLI Test",
                "output_dir": str(self.temp_dir / "output"),
                "device": "iPhone 16 Pro - Black Titanium - Portrait",
                "output_size": "iPhone6_9",
            },
            "screenshots": {
                "hero": {
                    "template": str(template_path),
                    "variables": {"headline": "Hello"},
                }
            },
        }
        config_path = self.temp_dir / "html_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        setup_calls = []

        def fake_prepare_html_environment(*, setup_requested, verbose, output_console):
            setup_calls.append(
                {
                    "setup_requested": setup_requested,
                    "verbose": verbose,
                    "console_type": type(output_console).__name__,
                }
            )

        class FakeGenerator:
            def generate_project(self, project_config, config_dir):
                return [Path(project_config.project.output_dir) / "hero.png"]

        monkeypatch.setattr(
            "koubou.cli._prepare_html_environment", fake_prepare_html_environment
        )
        monkeypatch.setattr("koubou.cli.ScreenshotGenerator", FakeGenerator)

        result = self.runner.invoke(
            app,
            ["generate", str(config_path), "--setup-html"],
        )

        assert result.exit_code == 0
        assert setup_calls == [
            {
                "setup_requested": True,
                "verbose": False,
                "console_type": "Console",
            }
        ]

    def test_generate_html_without_setup_shows_actionable_error(self, monkeypatch):
        """Test generate shows kou setup-html guidance when HTML is not ready."""
        template_path = self.temp_dir / "hero.html"
        template_path.write_text("<html><body>{{headline}}</body></html>")

        config_data = {
            "project": {
                "name": "HTML CLI Error Test",
                "output_dir": str(self.temp_dir / "output"),
                "device": "iPhone 16 Pro - Black Titanium - Portrait",
                "output_size": "iPhone6_9",
            },
            "screenshots": {
                "hero": {
                    "template": str(template_path),
                    "variables": {"headline": "Hello"},
                }
            },
        }
        config_path = self.temp_dir / "html_error_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        def fake_prepare_html_environment(*, setup_requested, verbose, output_console):
            raise RuntimeError(
                "HTML rendering is not set up yet. Run `kou setup-html`."
            )

        monkeypatch.setattr(
            "koubou.cli._prepare_html_environment", fake_prepare_html_environment
        )

        result = self.runner.invoke(app, ["generate", str(config_path)])

        assert result.exit_code == 1
        assert "kou setup-html" in result.stdout

    def test_live_with_setup_html(self, monkeypatch):
        """Test live --setup-html prepares HTML before live mode starts."""
        template_path = self.temp_dir / "hero.html"
        template_path.write_text("<html><body>{{headline}}</body></html>")

        config_data = {
            "project": {
                "name": "HTML Live Test",
                "output_dir": str(self.temp_dir / "output"),
                "device": "iPhone 16 Pro - Black Titanium - Portrait",
                "output_size": "iPhone6_9",
            },
            "screenshots": {
                "hero": {
                    "template": str(template_path),
                    "variables": {"headline": "Hello"},
                }
            },
        }
        config_path = self.temp_dir / "live_html_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        setup_calls = []

        def fake_prepare_html_environment(*, setup_requested, verbose, output_console):
            setup_calls.append(
                {
                    "setup_requested": setup_requested,
                    "verbose": verbose,
                    "console_type": type(output_console).__name__,
                }
            )

        class FakeResult:
            has_errors = False
            success_count = 1
            error_count = 0
            config_errors = []
            failed_screenshots = {}
            updated_preview_screenshots = []
            preview_errors = {}
            preview_full_reload = False

        class FakeLiveGenerator:
            def __init__(self, config_file):
                self.config_file = config_file
                self.preview_workspace = object()

            def initial_generation(self):
                return FakeResult()

            def get_asset_paths(self):
                return set()

            def get_dependency_summary(self):
                return {"total_dependencies": 0}

            def has_preview_screenshots(self):
                return True

            def sync_preview_workspace(self, screenshot_ids=None):
                return {}

            def get_preview_slides(self):
                return []

            def close(self):
                return None

        class FakeWatcher:
            def __init__(self, config_file, debounce_delay):
                self.config_file = config_file
                self.debounce_delay = debounce_delay

            def set_change_callback(self, callback):
                self.callback = callback

            def add_asset_paths(self, asset_paths):
                self.asset_paths = asset_paths

            def start(self):
                return None

            def stop(self):
                return None

            def get_watched_files(self):
                return set()

        class FakeLive:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def fake_signal(signum, handler):
            handler(signum, None)
            return None

        preview_servers = []

        class FakePreviewServer:
            def __init__(self, workspace):
                self.workspace = workspace
                self.url = "http://127.0.0.1:9999/"
                preview_servers.append(self)

            def set_slides(self, slides):
                self.slides = slides

            def start(self):
                return None

            def open_browser(self):
                return True

            def publish_slide_error(self, screenshot_id, error):
                return None

            def publish_reload_slides(self, screenshot_ids):
                return None

            def publish_full_reload(self):
                return None

            def stop(self):
                return None

        monkeypatch.setattr(
            "koubou.cli._prepare_html_environment", fake_prepare_html_environment
        )
        monkeypatch.setattr("koubou.cli.LiveScreenshotGenerator", FakeLiveGenerator)
        monkeypatch.setattr("koubou.cli.HtmlPreviewServer", FakePreviewServer)
        monkeypatch.setattr("koubou.cli.LiveWatcher", FakeWatcher)
        monkeypatch.setattr("koubou.cli.Live", FakeLive)
        monkeypatch.setattr("koubou.cli.signal.signal", fake_signal)
        monkeypatch.setattr(
            "koubou.cli._create_live_status_display",
            lambda: type("StatusDisplay", (), {"renderable": None})(),
        )
        monkeypatch.setattr("koubou.cli._update_live_status", lambda *args: None)

        result = self.runner.invoke(
            app,
            ["live", str(config_path), "--setup-html"],
        )

        assert result.exit_code == 0
        assert setup_calls == [
            {
                "setup_requested": True,
                "verbose": False,
                "console_type": "Console",
            }
        ]
        assert len(preview_servers) == 1

    def test_live_without_html_starts_image_preview(self, monkeypatch):
        """Test live without HTML config still starts the preview dashboard."""
        config_data = {
            "project": {
                "name": "Content Live Test",
                "output_dir": str(self.temp_dir / "output"),
                "device": "iPhone 16 Pro - Black Titanium - Portrait",
                "output_size": "iPhone6_9",
            },
            "screenshots": {
                "hero": {
                    "content": [
                        {
                            "type": "text",
                            "content": "Hello",
                            "position": ["50%", "50%"],
                        }
                    ]
                }
            },
        }
        config_path = self.temp_dir / "live_content_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        class FakeResult:
            has_errors = False
            success_count = 1
            error_count = 0
            config_errors = []
            failed_screenshots = {}
            updated_preview_screenshots = []
            preview_errors = {}
            preview_full_reload = False

        class FakeLiveGenerator:
            def __init__(self, config_file):
                self.config_file = config_file
                self.preview_workspace = object()

            def initial_generation(self):
                return FakeResult()

            def get_asset_paths(self):
                return set()

            def get_dependency_summary(self):
                return {"total_dependencies": 0}

            def has_preview_screenshots(self):
                return True

            def sync_preview_workspace(self, screenshot_ids=None):
                return {}

            def get_preview_slides(self):
                return []

            def close(self):
                return None

        class FakeWatcher:
            def __init__(self, config_file, debounce_delay):
                self.config_file = config_file
                self.debounce_delay = debounce_delay

            def set_change_callback(self, callback):
                self.callback = callback

            def add_asset_paths(self, asset_paths):
                self.asset_paths = asset_paths

            def start(self):
                return None

            def stop(self):
                return None

            def get_watched_files(self):
                return set()

        class FakeLive:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def fake_signal(signum, handler):
            handler(signum, None)
            return None

        preview_calls = []

        class FakePreviewServer:
            def __init__(self, workspace):
                self.url = "http://127.0.0.1:9999/"
                preview_calls.append(workspace)

            def set_slides(self, slides):
                self.slides = slides

            def start(self):
                return None

            def open_browser(self):
                return True

            def publish_slide_error(self, screenshot_id, error):
                return None

            def publish_reload_slides(self, screenshot_ids):
                return None

            def publish_full_reload(self):
                return None

            def stop(self):
                return None

        monkeypatch.setattr("koubou.cli.LiveScreenshotGenerator", FakeLiveGenerator)
        monkeypatch.setattr("koubou.cli.HtmlPreviewServer", FakePreviewServer)
        monkeypatch.setattr("koubou.cli.LiveWatcher", FakeWatcher)
        monkeypatch.setattr("koubou.cli.Live", FakeLive)
        monkeypatch.setattr("koubou.cli.signal.signal", fake_signal)
        monkeypatch.setattr(
            "koubou.cli._create_live_status_display",
            lambda: type("StatusDisplay", (), {"renderable": None})(),
        )
        monkeypatch.setattr("koubou.cli._update_live_status", lambda *args: None)

        result = self.runner.invoke(app, ["live", str(config_path)])

        assert result.exit_code == 0
        assert len(preview_calls) == 1

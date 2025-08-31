"""Tests for dependency analysis functionality."""

from pathlib import Path

from PIL import Image

from koubou.config import ContentItem, ProjectConfig, ProjectInfo, ScreenshotDefinition
from koubou.dependency_analyzer import AssetDependency, DependencyAnalyzer


class TestAssetDependency:
    """Tests for AssetDependency functionality."""

    def test_dependency_creation(self):
        """Test creating an asset dependency."""
        dep = AssetDependency("screenshot1", "path/to/image.png", "image")

        assert dep.screenshot_id == "screenshot1"
        assert dep.asset_path == "path/to/image.png"
        assert dep.asset_type == "image"
        assert dep.resolved_path is None
        assert dep.last_modified is None

    def test_resolve_path_absolute(self, tmp_path):
        """Test resolving absolute asset paths."""
        # Create test image
        image_path = tmp_path / "test_image.png"
        test_image = Image.new("RGB", (100, 100), "red")
        test_image.save(image_path)

        dep = AssetDependency("screenshot1", str(image_path), "image")

        assert dep.resolve_path(tmp_path) is True
        assert dep.resolved_path == image_path
        assert dep.last_modified is not None

    def test_resolve_path_relative(self, tmp_path):
        """Test resolving relative asset paths."""
        # Create test image
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        image_path = assets_dir / "test_image.png"
        test_image = Image.new("RGB", (100, 100), "blue")
        test_image.save(image_path)

        dep = AssetDependency("screenshot1", "assets/test_image.png", "image")

        assert dep.resolve_path(tmp_path) is True
        assert dep.resolved_path == image_path
        assert dep.last_modified is not None

    def test_resolve_path_nonexistent(self, tmp_path):
        """Test resolving paths to nonexistent files."""
        dep = AssetDependency("screenshot1", "nonexistent/path.png", "image")

        assert dep.resolve_path(tmp_path) is False
        assert dep.resolved_path is None
        assert dep.last_modified is None

    def test_has_changed_no_file(self):
        """Test change detection with no resolved file."""
        dep = AssetDependency("screenshot1", "path/to/image.png", "image")

        assert dep.has_changed() is False

    def test_has_changed_initial_check(self, tmp_path):
        """Test initial change detection sets modification time."""
        # Create test image
        image_path = tmp_path / "test_image.png"
        test_image = Image.new("RGB", (100, 100), "green")
        test_image.save(image_path)

        dep = AssetDependency("screenshot1", str(image_path), "image")
        dep.resolve_path(tmp_path)

        # First check should not report change but should set time
        assert dep.has_changed() is False
        assert dep.last_modified is not None


class TestDependencyAnalyzer:
    """Tests for DependencyAnalyzer functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = DependencyAnalyzer()

    def create_test_project(self, tmp_path) -> tuple[ProjectConfig, Path]:
        """Create a test project with assets."""
        # Create test assets
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()

        image1 = assets_dir / "welcome.png"
        image2 = assets_dir / "features.png"

        test_image = Image.new("RGB", (200, 400), "red")
        test_image.save(image1)
        test_image.save(image2)

        # Create project config
        project_config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir="output"),
            screenshots={
                "welcome_screen": ScreenshotDefinition(
                    name="Welcome Screen",
                    content=[
                        ContentItem(type="text", content="Welcome"),
                        ContentItem(
                            type="image",
                            asset="assets/welcome.png",
                            position=("50%", "50%"),
                        ),
                    ],
                ),
                "features_screen": ScreenshotDefinition(
                    name="Features Screen",
                    content=[
                        ContentItem(type="text", content="Features"),
                        ContentItem(
                            type="image",
                            asset="assets/features.png",
                            position=("50%", "50%"),
                        ),
                    ],
                ),
                "text_only_screen": ScreenshotDefinition(
                    name="Text Only Screen",
                    content=[ContentItem(type="text", content="Text Only")],
                ),
            },
        )

        return project_config, tmp_path

    def test_analyze_project_basic(self, tmp_path):
        """Test basic project analysis."""
        project_config, config_dir = self.create_test_project(tmp_path)

        self.analyzer.analyze_project(project_config, config_dir)

        # Should have 2 dependencies (2 images)
        assert len(self.analyzer.dependencies) == 2

        # Check screenshot-to-assets mapping
        welcome_assets = self.analyzer.get_screenshot_assets("welcome_screen")
        assert len(welcome_assets) == 1
        assert welcome_assets[0].asset_path == "assets/welcome.png"

        features_assets = self.analyzer.get_screenshot_assets("features_screen")
        assert len(features_assets) == 1
        assert features_assets[0].asset_path == "assets/features.png"

        # Text-only screen should have no assets
        text_assets = self.analyzer.get_screenshot_assets("text_only_screen")
        assert len(text_assets) == 0

    def test_get_asset_screenshots(self, tmp_path):
        """Test getting screenshots that depend on an asset."""
        project_config, config_dir = self.create_test_project(tmp_path)
        self.analyzer.analyze_project(project_config, config_dir)

        # Get screenshots that depend on welcome.png
        welcome_path = tmp_path / "assets" / "welcome.png"
        dependent_screenshots = self.analyzer.get_asset_screenshots(welcome_path)

        assert "welcome_screen" in dependent_screenshots
        assert "features_screen" not in dependent_screenshots

    def test_get_all_asset_paths(self, tmp_path):
        """Test getting all tracked asset paths."""
        project_config, config_dir = self.create_test_project(tmp_path)
        self.analyzer.analyze_project(project_config, config_dir)

        asset_paths = self.analyzer.get_all_asset_paths()

        assert len(asset_paths) == 2
        path_names = {path.name for path in asset_paths}
        assert "welcome.png" in path_names
        assert "features.png" in path_names

    def test_check_asset_changes_no_changes(self, tmp_path):
        """Test checking for asset changes when none occurred."""
        project_config, config_dir = self.create_test_project(tmp_path)
        self.analyzer.analyze_project(project_config, config_dir)

        # Initial check should find no changes
        changes = self.analyzer.check_asset_changes()
        assert changes == {}

    def test_validate_all_assets_valid(self, tmp_path):
        """Test validating assets when all exist."""
        project_config, config_dir = self.create_test_project(tmp_path)
        self.analyzer.analyze_project(project_config, config_dir)

        missing = self.analyzer.validate_all_assets()
        assert missing == {}

    def test_validate_all_assets_missing(self, tmp_path):
        """Test validating assets when some are missing."""
        project_config, config_dir = self.create_test_project(tmp_path)
        self.analyzer.analyze_project(project_config, config_dir)

        # Remove one asset file
        welcome_path = tmp_path / "assets" / "welcome.png"
        welcome_path.unlink()

        missing = self.analyzer.validate_all_assets()

        assert len(missing) == 1
        assert "assets/welcome.png" in missing
        assert "welcome_screen" in missing["assets/welcome.png"]

    def test_get_dependency_summary(self, tmp_path):
        """Test getting dependency summary."""
        project_config, config_dir = self.create_test_project(tmp_path)
        self.analyzer.analyze_project(project_config, config_dir)

        summary = self.analyzer.get_dependency_summary()

        assert summary["total_dependencies"] == 2
        assert summary["total_screenshots"] == 3  # Including text-only screen
        assert summary["total_assets"] == 2

        assert "welcome_screen" in summary["screenshot_to_assets"]
        assert "features_screen" in summary["screenshot_to_assets"]
        assert "text_only_screen" in summary["screenshot_to_assets"]

        assert len(summary["screenshot_to_assets"]["welcome_screen"]) == 1
        assert len(summary["screenshot_to_assets"]["text_only_screen"]) == 0

    def test_analyze_project_with_missing_assets(self, tmp_path):
        """Test project analysis with some missing assets."""
        # Create config with non-existent assets
        project_config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir="output"),
            screenshots={
                "screen1": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="image",
                            asset="nonexistent/image.png",
                            position=("50%", "50%"),
                        )
                    ]
                )
            },
        )

        self.analyzer.analyze_project(project_config, tmp_path)

        # Should have no dependencies due to missing asset
        assert len(self.analyzer.dependencies) == 0
        assert len(self.analyzer.get_screenshot_assets("screen1")) == 0

    def test_analyze_empty_project(self, tmp_path):
        """Test analyzing project with no screenshots."""
        project_config = ProjectConfig(
            project=ProjectInfo(name="Empty Project", output_dir="output"),
            screenshots={},
        )

        self.analyzer.analyze_project(project_config, tmp_path)

        assert len(self.analyzer.dependencies) == 0
        assert len(self.analyzer.get_all_asset_paths()) == 0

        summary = self.analyzer.get_dependency_summary()
        assert summary["total_dependencies"] == 0
        assert summary["total_screenshots"] == 0
        assert summary["total_assets"] == 0

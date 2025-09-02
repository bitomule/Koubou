"""Tests for localization functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from koubou.config import ContentItem, LocalizationConfig
from koubou.localization import LocalizedContentResolver, XCStringsManager


class TestLocalizationConfig:
    """Tests for LocalizationConfig model."""

    def test_valid_localization_config(self):
        """Test creating valid localization config."""
        config = LocalizationConfig(
            base_language="en",
            languages=["en", "es", "ja"],
            xcstrings_path="Localizable.xcstrings",
        )

        assert config.base_language == "en"
        assert config.languages == ["en", "es", "ja"]
        assert config.xcstrings_path == "Localizable.xcstrings"

    def test_default_xcstrings_path(self):
        """Test default xcstrings path."""
        config = LocalizationConfig(base_language="en", languages=["en", "es"])

        assert config.xcstrings_path == "Localizable.xcstrings"

    def test_empty_base_language_validation(self):
        """Test validation of empty base language."""
        with pytest.raises(ValueError, match="Base language cannot be empty"):
            LocalizationConfig(base_language="", languages=["en", "es"])

    def test_empty_languages_validation(self):
        """Test validation of empty languages list."""
        with pytest.raises(ValueError, match="Languages list cannot be empty"):
            LocalizationConfig(base_language="en", languages=[])

    def test_duplicate_languages_removal(self):
        """Test removal of duplicate languages."""
        config = LocalizationConfig(
            base_language="en", languages=["en", "es", "en", "ja", "es"]
        )

        assert config.languages == ["en", "es", "ja"]

    def test_base_language_not_in_languages(self):
        """Test validation that base language must be in languages list."""
        with pytest.raises(
            ValueError, match="Base language 'en' must be included in languages list"
        ):
            LocalizationConfig(base_language="en", languages=["es", "ja"])

    def test_language_whitespace_cleanup(self):
        """Test cleanup of whitespace in language codes."""
        config = LocalizationConfig(
            base_language=" en ", languages=[" en ", "  es  ", " ja "]
        )

        assert config.base_language == "en"
        assert config.languages == ["en", "es", "ja"]


class TestXCStringsManager:
    """Tests for XCStrings file management."""

    def setup_method(self):
        """Setup test method."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.localization_config = LocalizationConfig(
            base_language="en",
            languages=["en", "es", "ja"],
            xcstrings_path="test.xcstrings",
        )
        self.xcstrings_manager = XCStringsManager(
            self.localization_config, self.temp_dir
        )

    def teardown_method(self):
        """Cleanup after test."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_xcstrings_path_resolution(self):
        """Test xcstrings path resolution."""
        expected_path = self.temp_dir / "test.xcstrings"
        assert self.xcstrings_manager.xcstrings_path == expected_path

    def test_absolute_xcstrings_path(self):
        """Test absolute xcstrings path handling."""
        absolute_path = "/tmp/absolute.xcstrings"
        config = LocalizationConfig(
            base_language="en", languages=["en", "es"], xcstrings_path=absolute_path
        )
        manager = XCStringsManager(config, self.temp_dir)
        assert manager.xcstrings_path == Path(absolute_path)

    def test_create_xcstrings_file(self):
        """Test creating new xcstrings file."""
        text_keys = {"Welcome to App", "Settings", "Close"}

        self.xcstrings_manager.create_xcstrings_file(text_keys)

        # Verify file exists
        assert self.xcstrings_manager.xcstrings_path.exists()

        # Verify file content
        with open(self.xcstrings_manager.xcstrings_path) as f:
            data = json.load(f)

        assert data["sourceLanguage"] == "en"
        assert data["version"] == "1.0"
        assert len(data["strings"]) == 3

        # Check structure for one key
        welcome_entry = data["strings"]["Welcome to App"]
        assert "localizations" in welcome_entry

        localizations = welcome_entry["localizations"]
        assert len(localizations) == 3  # en, es, ja

        # English should be translated
        en_entry = localizations["en"]
        assert en_entry["stringUnit"]["state"] == "translated"
        assert en_entry["stringUnit"]["value"] == "Welcome to App"

        # Spanish should need translation
        es_entry = localizations["es"]
        assert es_entry["stringUnit"]["state"] == "needs_translation"
        assert es_entry["stringUnit"]["value"] == ""

    def test_load_nonexistent_xcstrings(self):
        """Test loading non-existent xcstrings file."""
        with pytest.raises(FileNotFoundError):
            self.xcstrings_manager.load_xcstrings()

    def test_load_malformed_xcstrings(self):
        """Test loading malformed xcstrings file."""
        # Create malformed JSON file
        with open(self.xcstrings_manager.xcstrings_path, "w") as f:
            f.write("{ invalid json")

        with pytest.raises(ValueError, match="Malformed XCStrings file"):
            self.xcstrings_manager.load_xcstrings()

    def test_update_xcstrings_with_new_keys(self):
        """Test updating existing xcstrings with new keys."""
        # Create initial file
        initial_keys = {"Welcome", "Settings"}
        self.xcstrings_manager.create_xcstrings_file(initial_keys)

        # Update with new keys
        new_keys = {"Welcome", "Settings", "About", "Help"}
        updated = self.xcstrings_manager.update_xcstrings_with_new_keys(new_keys)

        assert updated is True  # File was modified

        # Verify updated content
        with open(self.xcstrings_manager.xcstrings_path) as f:
            data = json.load(f)

        assert len(data["strings"]) == 4
        assert "About" in data["strings"]
        assert "Help" in data["strings"]

    def test_update_xcstrings_no_new_keys(self):
        """Test updating xcstrings when no new keys exist."""
        # Create initial file
        keys = {"Welcome", "Settings"}
        self.xcstrings_manager.create_xcstrings_file(keys)

        # Update with same keys
        updated = self.xcstrings_manager.update_xcstrings_with_new_keys(keys)

        assert updated is False  # File was not modified

    def test_get_translation_existing(self):
        """Test getting existing translation."""
        # Create xcstrings with manual translation
        xcstrings_data = {
            "sourceLanguage": "en",
            "strings": {
                "Hello": {
                    "localizations": {
                        "en": {"stringUnit": {"state": "translated", "value": "Hello"}},
                        "es": {"stringUnit": {"state": "translated", "value": "Hola"}},
                    }
                }
            },
            "version": "1.0",
        }

        # Write xcstrings file
        with open(self.xcstrings_manager.xcstrings_path, "w") as f:
            json.dump(xcstrings_data, f)

        # Load and test translations
        self.xcstrings_manager.load_xcstrings()

        assert self.xcstrings_manager.get_translation("Hello", "en") == "Hello"
        assert self.xcstrings_manager.get_translation("Hello", "es") == "Hola"

    def test_get_translation_missing_key(self):
        """Test getting translation for missing key."""
        # Create empty xcstrings
        self.xcstrings_manager.create_xcstrings_file(set())
        self.xcstrings_manager.load_xcstrings()

        # Should return original text for missing key
        assert self.xcstrings_manager.get_translation("Missing", "es") == "Missing"

    def test_get_translation_needs_translation(self):
        """Test getting translation that needs translation."""
        # Create xcstrings with untranslated key
        self.xcstrings_manager.create_xcstrings_file({"Hello"})
        self.xcstrings_manager.load_xcstrings()

        # Should return original text for untranslated
        assert self.xcstrings_manager.get_translation("Hello", "es") == "Hello"

    def test_xcstrings_exists(self):
        """Test checking if xcstrings file exists."""
        assert not self.xcstrings_manager.xcstrings_exists()

        self.xcstrings_manager.create_xcstrings_file({"Test"})
        assert self.xcstrings_manager.xcstrings_exists()

    def test_get_all_languages(self):
        """Test getting all configured languages."""
        languages = self.xcstrings_manager.get_all_languages()
        assert languages == ["en", "es", "ja"]


class TestLocalizedContentResolver:
    """Tests for localized content resolution."""

    def setup_method(self):
        """Setup test method."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.localization_config = LocalizationConfig(
            base_language="en", languages=["en", "es"], xcstrings_path="test.xcstrings"
        )
        self.xcstrings_manager = XCStringsManager(
            self.localization_config, self.temp_dir
        )
        self.content_resolver = LocalizedContentResolver(self.xcstrings_manager)

    def teardown_method(self):
        """Cleanup after test."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_extract_text_keys_from_content(self):
        """Test extracting text keys from content items."""
        content_items = [
            ContentItem(type="text", content="Welcome to App"),
            ContentItem(type="image", asset="image.png"),
            ContentItem(type="text", content="Settings"),
            ContentItem(type="text", content=""),  # Empty content
        ]

        text_keys = self.content_resolver.extract_text_keys_from_content(content_items)

        assert text_keys == {"Welcome to App", "Settings"}

    def test_localize_content_items(self):
        """Test localizing content items."""
        # Create xcstrings with translations
        xcstrings_data = {
            "sourceLanguage": "en",
            "strings": {
                "Welcome": {
                    "localizations": {
                        "en": {
                            "stringUnit": {"state": "translated", "value": "Welcome"}
                        },
                        "es": {
                            "stringUnit": {"state": "translated", "value": "Bienvenido"}
                        },
                    }
                }
            },
            "version": "1.0",
        }

        with open(self.xcstrings_manager.xcstrings_path, "w") as f:
            json.dump(xcstrings_data, f)

        self.xcstrings_manager.load_xcstrings()

        # Create content items
        content_items = [
            ContentItem(type="text", content="Welcome", size=24),
            ContentItem(type="image", asset="test.png"),
        ]

        # Localize to Spanish
        localized_items = self.content_resolver.localize_content_items(
            content_items, "es"
        )

        assert len(localized_items) == 2
        assert localized_items[0].content == "Bienvenido"
        assert localized_items[0].size == 24  # Other properties preserved
        assert localized_items[1].type == "image"  # Non-text items unchanged

    def test_localize_content_items_no_translation(self):
        """Test localizing when no translation available."""
        # Create xcstrings without Spanish translation
        self.xcstrings_manager.create_xcstrings_file({"Hello"})
        self.xcstrings_manager.load_xcstrings()

        content_items = [
            ContentItem(type="text", content="Hello"),
        ]

        # Localize to Spanish (no translation available)
        localized_items = self.content_resolver.localize_content_items(
            content_items, "es"
        )

        assert len(localized_items) == 1
        assert localized_items[0].content == "Hello"  # Falls back to original

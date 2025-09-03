"""XCStrings localization file management and text content localization."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

from .config import LocalizationConfig

logger = logging.getLogger(__name__)


class XCStringsManager:
    """Manages XCStrings localization files for screenshot content localization."""

    def __init__(self, localization_config: LocalizationConfig, config_dir: Path):
        """Initialize XCStrings manager.

        Args:
            localization_config: Localization configuration
            config_dir: Directory containing the config file for path resolution
        """
        self.config = localization_config
        self.config_dir = config_dir

        if Path(localization_config.xcstrings_path).is_absolute():
            self.xcstrings_path = Path(localization_config.xcstrings_path)
        else:
            self.xcstrings_path = config_dir / localization_config.xcstrings_path

        self._xcstrings_data: Optional[Dict] = None

    def load_xcstrings(self) -> Dict:
        """Load xcstrings data from file.

        Returns:
            Parsed xcstrings data dictionary

        Raises:
            FileNotFoundError: If xcstrings file doesn't exist
            ValueError: If xcstrings file is malformed
        """
        if not self.xcstrings_path.exists():
            raise FileNotFoundError(f"XCStrings file not found: {self.xcstrings_path}")

        try:
            with open(self.xcstrings_path, "r", encoding="utf-8") as f:
                self._xcstrings_data = json.load(f)
                logger.info(f"Loaded XCStrings file: {self.xcstrings_path}")
                return self._xcstrings_data
        except json.JSONDecodeError as e:
            raise ValueError(f"Malformed XCStrings file {self.xcstrings_path}: {e}")
        except Exception as e:
            raise ValueError(
                f"Failed to load XCStrings file {self.xcstrings_path}: {e}"
            )

    def create_xcstrings_file(self, text_keys: Set[str]) -> None:
        """Create a new xcstrings file with the provided text keys.

        Args:
            text_keys: Set of text strings to use as localization keys
        """
        logger.info(
            f"Creating XCStrings file with {len(text_keys)} keys: {self.xcstrings_path}"
        )

        xcstrings_data = {
            "sourceLanguage": self.config.base_language,
            "strings": {},
            "version": "1.0",
        }

        # Add each text key with base language translation and empty target languages
        for text_key in sorted(text_keys):
            localizations = {}

            # Base language gets the text as-is with "translated" state
            localizations[self.config.base_language] = {
                "stringUnit": {"state": "translated", "value": text_key}
            }

            # Other languages get empty value with "needs_translation" state
            for language in self.config.languages:
                if language != self.config.base_language:
                    localizations[language] = {
                        "stringUnit": {"state": "needs_translation", "value": ""}
                    }

            xcstrings_data["strings"][text_key] = {"localizations": localizations}

        self.xcstrings_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.xcstrings_path, "w", encoding="utf-8") as f:
            json.dump(xcstrings_data, f, indent=2, ensure_ascii=False)

        self._xcstrings_data = xcstrings_data
        logger.info(f"Created XCStrings file: {self.xcstrings_path}")

    def update_xcstrings_with_new_keys(self, text_keys: Set[str]) -> bool:
        """Update existing xcstrings file with new text keys.

        Args:
            text_keys: Set of text strings to ensure are in xcstrings

        Returns:
            True if file was modified, False if no changes needed

        Raises:
            ValueError: If xcstrings file is malformed
        """
        if not self.xcstrings_path.exists():
            self.create_xcstrings_file(text_keys)
            return True

        # Load existing xcstrings
        xcstrings_data = self.load_xcstrings()
        existing_keys = set(xcstrings_data.get("strings", {}).keys())
        new_keys = text_keys - existing_keys

        if not new_keys:
            logger.info("No new keys to add to XCStrings file")
            return False

        logger.info(f"Adding {len(new_keys)} new keys to XCStrings file")

        for text_key in sorted(new_keys):
            localizations = {}

            # Base language gets the text as-is
            localizations[self.config.base_language] = {
                "stringUnit": {"state": "translated", "value": text_key}
            }

            # Other languages get empty value
            for language in self.config.languages:
                if language != self.config.base_language:
                    localizations[language] = {
                        "stringUnit": {"state": "needs_translation", "value": ""}
                    }

            xcstrings_data["strings"][text_key] = {"localizations": localizations}

        # Write updated file
        with open(self.xcstrings_path, "w", encoding="utf-8") as f:
            json.dump(xcstrings_data, f, indent=2, ensure_ascii=False)

        self._xcstrings_data = xcstrings_data
        return True

    def get_translation(self, text_key: str, language: str) -> str:
        """Get translation for a text key in specified language.

        Args:
            text_key: The text key to translate
            language: Target language code

        Returns:
            Translated text, or original text if translation not found
        """
        if not self._xcstrings_data:
            try:
                self.load_xcstrings()
            except (FileNotFoundError, ValueError):
                # If xcstrings file doesn't exist or is malformed, return original text
                return text_key

        strings_data = self._xcstrings_data.get("strings", {})
        if text_key not in strings_data:
            logger.warning(f"Text key '{text_key}' not found in XCStrings file")
            return text_key

        localizations = strings_data[text_key].get("localizations", {})
        if language not in localizations:
            logger.warning(f"Language '{language}' not found for key '{text_key}'")
            return text_key

        localization = localizations[language]
        string_unit = localization.get("stringUnit", {})
        translated_value = string_unit.get("value", "")

        # If translation is empty or marked as needing translation, return original
        if not translated_value or string_unit.get("state") == "needs_translation":
            logger.debug(
                f"No translation available for '{text_key}' in '{language}', "
                f"using original"
            )
            return text_key

        return translated_value

    def get_all_languages(self) -> List[str]:
        """Get all languages configured for this localization.

        Returns:
            List of language codes
        """
        return self.config.languages

    def xcstrings_exists(self) -> bool:
        """Check if xcstrings file exists.

        Returns:
            True if xcstrings file exists
        """
        return self.xcstrings_path.exists()


class LocalizedContentResolver:
    """Resolves localized content for screenshot generation."""

    def __init__(self, xcstrings_manager: XCStringsManager):
        """Initialize content resolver.

        Args:
            xcstrings_manager: XCStrings manager instance
        """
        self.xcstrings_manager = xcstrings_manager

    def extract_text_keys_from_content(self, content_items: List) -> Set[str]:
        """Extract all text keys from content items.

        Args:
            content_items: List of content items from screenshot definition

        Returns:
            Set of text strings that need localization
        """
        text_keys = set()

        for item in content_items:
            if item.type == "text" and item.content:
                text_keys.add(item.content)

        return text_keys

    def localize_content_items(self, content_items: List, language: str) -> List:
        """Create localized version of content items for specified language.

        Args:
            content_items: Original content items
            language: Target language code

        Returns:
            List of content items with localized text
        """
        localized_items = []

        for item in content_items:
            # Create a copy of the item
            if item.type == "text" and item.content:
                # Get localized text
                localized_text = self.xcstrings_manager.get_translation(
                    item.content, language
                )

                # Create new item with localized content
                from copy import deepcopy

                localized_item = deepcopy(item)
                localized_item.content = localized_text
                localized_items.append(localized_item)
            else:
                # Non-text items remain unchanged
                localized_items.append(item)

        return localized_items

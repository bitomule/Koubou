"""Tests for file watching functionality."""

import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from koubou.watcher import DebounceHandler, LiveWatcher


class TestDebounceHandler:
    """Tests for DebounceHandler functionality."""

    def test_handler_creation(self):
        """Test creating a debounce handler."""
        callback = MagicMock()
        handler = DebounceHandler(callback, debounce_delay=0.1)

        assert handler.callback == callback
        assert handler.debounce_delay == 0.1
        assert len(handler._pending_files) == 0

    def test_is_temp_file_patterns(self):
        """Test temporary file detection patterns."""
        callback = MagicMock()
        handler = DebounceHandler(callback)

        # Test various temp file patterns
        assert handler._is_temp_file(Path("file.swp")) is True
        assert handler._is_temp_file(Path("file.swo")) is True
        assert handler._is_temp_file(Path("file.tmp")) is True
        assert handler._is_temp_file(Path("file~")) is True
        assert handler._is_temp_file(Path(".DS_Store")) is True
        assert handler._is_temp_file(Path("__pycache__/module.pyc")) is True

        # Hidden files (except allowed ones)
        assert handler._is_temp_file(Path(".hidden_file")) is True
        assert handler._is_temp_file(Path(".gitignore")) is False  # Allowed
        assert handler._is_temp_file(Path(".env")) is False  # Allowed

        # Normal files
        assert handler._is_temp_file(Path("normal_file.txt")) is False
        assert handler._is_temp_file(Path("config.yaml")) is False

    def test_debounce_single_file(self):
        """Test debouncing behavior with a single file change."""
        callback = MagicMock()
        handler = DebounceHandler(callback, debounce_delay=0.05)

        # Create mock event
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = "/path/to/test_file.txt"

        # Trigger modification
        handler.on_modified(mock_event)

        # Should not call immediately
        assert not callback.called

        # Wait for debounce
        time.sleep(0.1)

        # Should have called callback with the file
        callback.assert_called_once()
        called_files = callback.call_args[0][0]
        assert Path("/path/to/test_file.txt") in called_files

    def test_debounce_multiple_rapid_changes(self):
        """Test debouncing with rapid successive changes."""
        callback = MagicMock()
        handler = DebounceHandler(callback, debounce_delay=0.05)

        # Create mock events
        files = ["/path/to/file1.txt", "/path/to/file2.txt", "/path/to/file3.txt"]

        for file_path in files:
            mock_event = MagicMock()
            mock_event.is_directory = False
            mock_event.src_path = file_path
            handler.on_modified(mock_event)
            time.sleep(0.01)  # Rapid changes

        # Should not call immediately
        assert not callback.called

        # Wait for debounce
        time.sleep(0.1)

        # Should have called once with all files
        callback.assert_called_once()
        called_files = callback.call_args[0][0]
        assert len(called_files) == 3
        for file_path in files:
            assert Path(file_path) in called_files

    def test_ignore_temporary_files(self):
        """Test that temporary files are ignored."""
        callback = MagicMock()
        handler = DebounceHandler(callback, debounce_delay=0.05)

        # Create mock event for temp file
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = "/path/to/file.swp"

        handler.on_modified(mock_event)

        # Wait for potential debounce
        time.sleep(0.1)

        # Should not have called callback
        assert not callback.called

    def test_ignore_directories(self):
        """Test that directory events are ignored."""
        callback = MagicMock()
        handler = DebounceHandler(callback, debounce_delay=0.05)

        # Create mock event for directory
        mock_event = MagicMock()
        mock_event.is_directory = True
        mock_event.src_path = "/path/to/directory"

        handler.on_modified(mock_event)

        # Wait for potential debounce
        time.sleep(0.1)

        # Should not have called callback
        assert not callback.called

    def test_cleanup(self):
        """Test handler cleanup."""
        callback = MagicMock()
        handler = DebounceHandler(callback, debounce_delay=0.05)

        # Create mock event to start timer
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = "/path/to/file.txt"
        handler.on_modified(mock_event)

        # Cleanup should cancel timer
        handler.cleanup()

        # Wait to ensure timer would have fired
        time.sleep(0.1)

        # Callback should not be called after cleanup
        assert not callback.called

    def test_on_created_event(self):
        """Test handling file creation events."""
        callback = MagicMock()
        handler = DebounceHandler(callback, debounce_delay=0.05)

        # Create mock creation event
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = "/path/to/new_file.txt"

        handler.on_created(mock_event)

        # Wait for debounce
        time.sleep(0.1)

        # Should have called callback
        callback.assert_called_once()
        called_files = callback.call_args[0][0]
        assert Path("/path/to/new_file.txt") in called_files


class TestLiveWatcher:
    """Tests for LiveWatcher functionality."""

    def test_watcher_creation(self, tmp_path):
        """Test creating a live watcher."""
        config_file = tmp_path / "config.yaml"
        config_file.touch()

        watcher = LiveWatcher(config_file, debounce_delay=0.1)

        assert watcher.config_file == config_file.resolve()
        assert watcher.debounce_delay == 0.1
        assert watcher._change_callback is None

    def test_set_change_callback(self, tmp_path):
        """Test setting the change callback."""
        config_file = tmp_path / "config.yaml"
        config_file.touch()

        watcher = LiveWatcher(config_file)
        callback = MagicMock()

        watcher.set_change_callback(callback)
        assert watcher._change_callback == callback

    def test_add_asset_paths(self, tmp_path):
        """Test adding asset paths to watch."""
        config_file = tmp_path / "config.yaml"
        config_file.touch()

        # Create test assets
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        asset1 = assets_dir / "image1.png"
        asset2 = assets_dir / "image2.png"
        asset1.touch()
        asset2.touch()

        watcher = LiveWatcher(config_file)

        # Add asset paths
        asset_paths = {asset1, asset2}
        watcher.add_asset_paths(asset_paths)

        assert len(watcher._watched_paths) == 2
        assert asset1.resolve() in watcher._watched_paths
        assert asset2.resolve() in watcher._watched_paths

    def test_add_nonexistent_asset_paths(self, tmp_path):
        """Test adding paths to non-existent assets."""
        config_file = tmp_path / "config.yaml"
        config_file.touch()

        watcher = LiveWatcher(config_file)

        # Add non-existent paths
        nonexistent_paths = {
            tmp_path / "nonexistent1.png",
            tmp_path / "nonexistent2.png",
        }
        watcher.add_asset_paths(nonexistent_paths)

        # Should not add non-existent paths
        assert len(watcher._watched_paths) == 0

    def test_get_watched_files(self, tmp_path):
        """Test getting all watched files."""
        config_file = tmp_path / "config.yaml"
        config_file.touch()

        asset_file = tmp_path / "asset.png"
        asset_file.touch()

        watcher = LiveWatcher(config_file)
        watcher.add_asset_paths({asset_file})

        watched_files = watcher.get_watched_files()

        assert config_file.resolve() in watched_files
        assert asset_file.resolve() in watched_files
        assert len(watched_files) == 2

    def test_get_status(self, tmp_path):
        """Test getting watcher status."""
        config_file = tmp_path / "config.yaml"
        config_file.touch()

        watcher = LiveWatcher(config_file, debounce_delay=0.5)

        status = watcher.get_status()

        assert status["is_running"] is False
        assert status["config_file"] == str(config_file.resolve())
        assert status["watched_assets"] == 0
        assert status["watched_directories"] == 0
        assert status["debounce_delay"] == 0.5

    def test_get_asset_directories(self, tmp_path):
        """Test getting unique asset directories."""
        config_file = tmp_path / "config.yaml"
        config_file.touch()

        # Create assets in different directories
        assets_dir1 = tmp_path / "assets1"
        assets_dir2 = tmp_path / "assets2"
        assets_dir1.mkdir()
        assets_dir2.mkdir()

        asset1 = assets_dir1 / "image1.png"
        asset2 = assets_dir1 / "image2.png"  # Same directory
        asset3 = assets_dir2 / "image3.png"
        asset1.touch()
        asset2.touch()
        asset3.touch()

        watcher = LiveWatcher(config_file)
        watcher.add_asset_paths({asset1, asset2, asset3})

        asset_dirs = watcher._get_asset_directories()

        assert len(asset_dirs) == 2
        assert assets_dir1 in asset_dirs
        assert assets_dir2 in asset_dirs

    def test_start_without_callback_raises_error(self, tmp_path):
        """Test that starting without callback raises error."""
        config_file = tmp_path / "config.yaml"
        config_file.touch()

        watcher = LiveWatcher(config_file)

        with pytest.raises(ValueError, match="Change callback must be set"):
            watcher.start()

    def test_start_and_stop_basic(self, tmp_path):
        """Test basic start and stop functionality."""
        config_file = tmp_path / "config.yaml"
        config_file.touch()

        watcher = LiveWatcher(config_file)
        callback = MagicMock()
        watcher.set_change_callback(callback)

        # Start watcher
        watcher.start()
        assert watcher.get_status()["is_running"] is True

        # Stop watcher
        watcher.stop()

        # Brief wait for cleanup
        time.sleep(0.1)
        assert watcher.get_status()["is_running"] is False

    def test_double_start_warning(self, tmp_path, caplog):
        """Test warning when trying to start already running watcher."""
        config_file = tmp_path / "config.yaml"
        config_file.touch()

        watcher = LiveWatcher(config_file)
        callback = MagicMock()
        watcher.set_change_callback(callback)

        # Start watcher
        watcher.start()

        # Try to start again
        watcher.start()

        # Should log warning
        assert "already running" in caplog.text

        # Cleanup
        watcher.stop()

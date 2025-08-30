"""File system watcher for live editing functionality."""

import logging
import time
from pathlib import Path
from threading import Event, Timer
from typing import Any, Callable, Dict, Optional, Set

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class DebounceHandler(FileSystemEventHandler):
    """File system event handler with debouncing to prevent excessive calls."""

    def __init__(
        self, callback: Callable[[Set[Path]], None], debounce_delay: float = 0.5
    ):
        """Initialize debounce handler.

        Args:
            callback: Function to call with set of changed file paths
            debounce_delay: Delay in seconds before calling callback
        """
        super().__init__()
        self.callback = callback
        self.debounce_delay = debounce_delay
        self._pending_files: Set[Path] = set()
        self._timer: Optional[Timer] = None
        self._temp_file_patterns = {
            ".swp",
            ".swo",
            ".tmp",
            ".temp",
            "~",  # Editor temporary files
            ".DS_Store",  # macOS system files
            "__pycache__",  # Python cache
        }

    def _is_temp_file(self, file_path: Path) -> bool:
        """Check if a file should be ignored as a temporary file.

        Args:
            file_path: Path to check

        Returns:
            True if file should be ignored
        """
        # Check filename patterns
        name = file_path.name
        full_path = str(file_path)
        if any(name.endswith(pattern) for pattern in self._temp_file_patterns):
            return True
        if any(pattern in name for pattern in self._temp_file_patterns):
            return True
        if any(pattern in full_path for pattern in self._temp_file_patterns):
            return True

        # Check for hidden files (starting with .)
        if name.startswith(".") and name not in [".gitignore", ".env"]:
            return True

        return False

    def _schedule_callback(self) -> None:
        """Schedule the callback to be called after debounce delay."""
        # Cancel existing timer
        if self._timer:
            self._timer.cancel()

        # Schedule new timer
        self._timer = Timer(self.debounce_delay, self._execute_callback)
        self._timer.start()

    def _execute_callback(self) -> None:
        """Execute the callback with pending files."""
        if self._pending_files:
            files_to_process = self._pending_files.copy()
            self._pending_files.clear()

            logger.debug(
                f"Processing {len(files_to_process)} changed files after debounce"
            )
            try:
                self.callback(files_to_process)
            except Exception as e:
                logger.error(f"Error in file change callback: {e}")

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if event.is_directory:
            return

        file_path = Path(str(event.src_path))

        # Skip temporary files
        if self._is_temp_file(file_path):
            logger.debug(f"Ignoring temp file: {file_path}")
            return

        logger.debug(f"File modified: {file_path}")
        self._pending_files.add(file_path)
        self._schedule_callback()

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if event.is_directory:
            return

        file_path = Path(str(event.src_path))

        # Skip temporary files
        if self._is_temp_file(file_path):
            return

        logger.debug(f"File created: {file_path}")
        self._pending_files.add(file_path)
        self._schedule_callback()

    def cleanup(self) -> None:
        """Clean up any pending timers."""
        if self._timer:
            self._timer.cancel()


class LiveWatcher:
    """Watches config file and asset files for changes during live editing."""

    def __init__(self, config_file: Path, debounce_delay: float = 0.5):
        """Initialize live watcher.

        Args:
            config_file: Path to the YAML config file to watch
            debounce_delay: Delay in seconds before processing changes
        """
        self.config_file = config_file.resolve()
        self.debounce_delay = debounce_delay

        # File watching state
        self._observer: Optional[Observer] = None
        self._handler: Optional[DebounceHandler] = None
        self._watched_paths: Set[Path] = set()
        self._stop_event = Event()

        # Callbacks
        self._change_callback: Optional[Callable[[Set[Path]], None]] = None

        logger.info(f"Initialized live watcher for config: {self.config_file}")

    def set_change_callback(self, callback: Callable[[Set[Path]], None]) -> None:
        """Set callback function to be called when files change.

        Args:
            callback: Function that accepts a set of changed file paths
        """
        self._change_callback = callback

    def add_asset_paths(self, asset_paths: Set[Path]) -> None:
        """Add asset file paths to watch for changes.

        Args:
            asset_paths: Set of asset file paths to monitor
        """
        new_paths = set()

        for asset_path in asset_paths:
            resolved_path = asset_path.resolve()
            if resolved_path.exists() and resolved_path not in self._watched_paths:
                new_paths.add(resolved_path)

        if new_paths:
            self._watched_paths.update(new_paths)
            logger.info(f"Added {len(new_paths)} asset paths to watch list")

            # If already watching, restart to include new paths
            if self._observer and self._observer.is_alive():
                logger.debug("Restarting watcher to include new asset paths")
                self._restart_watcher()

    def start(self) -> None:
        """Start watching for file changes."""
        if self._observer and self._observer.is_alive():
            logger.warning("Watcher is already running")
            return

        if not self._change_callback:
            raise ValueError("Change callback must be set before starting watcher")

        # Create handler
        self._handler = DebounceHandler(
            callback=self._change_callback, debounce_delay=self.debounce_delay
        )

        # Create observer
        self._observer = Observer()

        # Watch config file directory
        config_dir = self.config_file.parent
        self._observer.schedule(self._handler, str(config_dir), recursive=False)
        logger.info(f"Watching config directory: {config_dir}")

        # Watch asset directories
        asset_dirs = self._get_asset_directories()
        for asset_dir in asset_dirs:
            self._observer.schedule(self._handler, str(asset_dir), recursive=True)
            logger.info(f"Watching asset directory: {asset_dir}")

        # Start watching
        self._observer.start()
        logger.info("Live watcher started")

    def stop(self) -> None:
        """Stop watching for file changes."""
        if self._observer and self._observer.is_alive():
            self._observer.stop()
            self._observer.join(timeout=2.0)
            logger.info("Live watcher stopped")

        if self._handler:
            self._handler.cleanup()

        self._stop_event.set()

    def wait_for_stop(self) -> None:
        """Wait for the watcher to be stopped."""
        self._stop_event.wait()

    def _get_asset_directories(self) -> Set[Path]:
        """Get unique directories containing asset files.

        Returns:
            Set of directories to watch
        """
        asset_dirs = set()

        for asset_path in self._watched_paths:
            if asset_path.exists():
                asset_dirs.add(asset_path.parent)

        return asset_dirs

    def _restart_watcher(self) -> None:
        """Restart the watcher to pick up new paths."""
        was_running = self._observer and self._observer.is_alive()

        if was_running:
            self.stop()
            time.sleep(0.1)  # Brief pause to ensure cleanup
            self.start()

    def get_watched_files(self) -> Set[Path]:
        """Get all files currently being watched.

        Returns:
            Set of all watched file paths
        """
        watched = {self.config_file}
        watched.update(self._watched_paths)
        return watched

    def get_status(self) -> Dict[str, Any]:
        """Get current watcher status.

        Returns:
            Dictionary with watcher status information
        """
        return {
            "is_running": bool(self._observer and self._observer.is_alive()),
            "config_file": str(self.config_file),
            "watched_assets": len(self._watched_paths),
            "watched_directories": len(self._get_asset_directories()),
            "debounce_delay": self.debounce_delay,
        }

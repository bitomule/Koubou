"""HTML template renderer using Playwright headless browser."""

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple

from ..html_setup import (
    browser_setup_message,
    import_sync_playwright,
)
from .html_staging import stage_html_workspace

logger = logging.getLogger(__name__)


class HtmlRenderer:
    """Renders HTML templates to PNG via Playwright headless browser."""

    def __init__(self):
        self._playwright = None
        self._browser = None

    def _ensure_browser(self):
        if self._browser:
            return

        sync_playwright = import_sync_playwright()
        self._playwright = sync_playwright().start()

        # Try system Chrome first, fall back to Playwright's chromium
        try:
            self._browser = self._playwright.chromium.launch(channel="chrome")
            logger.info("Using system Chrome for HTML rendering")
        except Exception:
            try:
                self._browser = self._playwright.chromium.launch()
                logger.info("Using Playwright Chromium for HTML rendering")
            except Exception as e:
                raise RuntimeError(browser_setup_message(str(e)))

    def render(
        self,
        template_path: Path,
        variables: Dict[str, str],
        size: Tuple[int, int],
        assets: Optional[Dict[str, str]] = None,
    ) -> bytes:
        """Render an HTML template to PNG bytes.

        Args:
            template_path: Path to the HTML template file
            variables: Dict of {{key}} -> value substitutions
            size: (width, height) viewport size in pixels
            assets: Dict of {relative_name: absolute_path} to symlink into sandbox

        Returns:
            PNG image bytes
        """
        self._ensure_browser()
        assert self._browser is not None

        tmpdir = tempfile.mkdtemp(prefix="koubou_html_")
        try:
            tmpdir_path = Path(tmpdir)
            width, height = size
            index_path = stage_html_workspace(
                template_path=template_path,
                variables=variables,
                destination_dir=tmpdir_path,
                assets=assets,
            )

            # Render with Playwright
            png_bytes = self.render_staged(index_path.parent, size)

            logger.info(
                f"Rendered HTML template {template_path.name} " f"at {width}x{height}"
            )
            return png_bytes

        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def render_staged(self, workspace_dir: Path, size: Tuple[int, int]) -> bytes:
        """Render a pre-staged HTML workspace directory to PNG bytes."""
        self._ensure_browser()
        assert self._browser is not None

        width, height = size
        page = self._browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=1,
        )
        try:
            page.goto(
                f"file://{workspace_dir / 'index.html'}", wait_until="networkidle"
            )
            return page.screenshot(type="png", full_page=False)
        finally:
            page.close()

    def close(self):
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

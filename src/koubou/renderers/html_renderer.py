"""HTML template renderer using Playwright headless browser."""

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def _import_playwright():
    try:
        from playwright.sync_api import sync_playwright

        return sync_playwright
    except ImportError:
        raise RuntimeError(
            "Playwright is required for HTML template rendering. "
            "Install it with: pip install koubou[html]\n"
            "Then install a browser: playwright install chromium"
        )


class HtmlRenderer:
    """Renders HTML templates to PNG via Playwright headless browser."""

    def __init__(self):
        self._playwright = None
        self._browser = None

    def _ensure_browser(self):
        if self._browser:
            return

        sync_playwright = _import_playwright()
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
                raise RuntimeError(
                    f"No browser available for HTML rendering: {e}\n"
                    "Install Chrome or run: playwright install chromium"
                )

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

            # Mount template sibling files (CSS, JS, images, etc.)
            template_dir = template_path.parent.resolve()
            for item in template_dir.iterdir():
                if item == template_path.resolve():
                    continue
                dest = tmpdir_path / item.name
                if not dest.exists():
                    try:
                        os.symlink(item, dest)
                    except OSError:
                        if item.is_dir():
                            shutil.copytree(item, dest)
                        else:
                            shutil.copy2(item, dest)

            # Mount explicit assets (override sibling files if name conflicts)
            if assets:
                for rel_name, abs_path in assets.items():
                    dest = tmpdir_path / rel_name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if dest.exists() or dest.is_symlink():
                        dest.unlink()
                    try:
                        os.symlink(abs_path, dest)
                    except OSError:
                        shutil.copy2(abs_path, dest)

            # Read and process template
            html_content = template_path.read_text(encoding="utf-8")
            for key, value in variables.items():
                html_content = html_content.replace(f"{{{{{key}}}}}", value)

            # Write processed HTML (overwrites any sibling with same name)
            index_path = tmpdir_path / "index.html"
            index_path.write_text(html_content, encoding="utf-8")

            # Render with Playwright
            width, height = size
            page = self._browser.new_page(
                viewport={"width": width, "height": height},
                device_scale_factor=1,
            )
            try:
                page.goto(f"file://{index_path}", wait_until="networkidle")
                png_bytes = page.screenshot(type="png", full_page=False)
            finally:
                page.close()

            logger.info(
                f"Rendered HTML template {template_path.name} " f"at {width}x{height}"
            )
            return png_bytes

        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def close(self):
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

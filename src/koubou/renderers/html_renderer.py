"""HTML template renderer using Playwright headless browser."""

from dataclasses import dataclass
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..html_setup import (
    browser_setup_message,
    import_sync_playwright,
)
from .html_staging import stage_html_workspace

logger = logging.getLogger(__name__)


@dataclass
class HtmlRenderResult:
    """Rendered PNG bytes plus compact layout metadata."""

    png_bytes: bytes
    layout: Dict[str, Any]


def _round_ratio(value: float) -> float:
    """Round normalized values for smaller, stable JSON payloads."""
    return round(value, 4)


def _clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def _normalize_box(
    raw_element: Dict[str, Any], canvas_width: int, canvas_height: int
) -> Dict[str, float]:
    """Clip an element rect to the canvas and normalize it to 0..1 ratios."""
    left = _clamp(float(raw_element["left"]), 0.0, float(canvas_width))
    top = _clamp(float(raw_element["top"]), 0.0, float(canvas_height))
    right = _clamp(float(raw_element["right"]), 0.0, float(canvas_width))
    bottom = _clamp(float(raw_element["bottom"]), 0.0, float(canvas_height))

    if right < left:
        right = left
    if bottom < top:
        bottom = top

    return {
        "x": left / canvas_width,
        "y": top / canvas_height,
        "width": (right - left) / canvas_width,
        "height": (bottom - top) / canvas_height,
    }


def _build_layout_manifest(
    raw_elements: List[Dict[str, Any]], size: Tuple[int, int]
) -> Dict[str, Any]:
    """Convert raw DOM measurements into the compact JSON layout contract."""
    canvas_width, canvas_height = size
    normalized_elements: List[Dict[str, Any]] = []
    overlap_boxes: List[Tuple[str, Dict[str, float]]] = []

    for raw_element in raw_elements:
        box = _normalize_box(raw_element, canvas_width, canvas_height)
        element: Dict[str, Any] = {
            "id": raw_element["id"],
            "x": _round_ratio(box["x"]),
            "y": _round_ratio(box["y"]),
            "width": _round_ratio(box["width"]),
            "height": _round_ratio(box["height"]),
        }

        role = raw_element.get("role")
        if role:
            element["role"] = role

        text = raw_element.get("text")
        if text:
            element["text"] = text

        src = raw_element.get("src")
        if src:
            element["src"] = src

        z_index = raw_element.get("zIndex")
        if z_index is not None:
            element["zIndex"] = z_index

        normalized_elements.append(element)
        overlap_boxes.append((raw_element["id"], box))

    overlaps: List[Dict[str, Any]] = []
    for index, (first_id, first_box) in enumerate(overlap_boxes):
        first_right = first_box["x"] + first_box["width"]
        first_bottom = first_box["y"] + first_box["height"]

        for second_id, second_box in overlap_boxes[index + 1 :]:
            second_right = second_box["x"] + second_box["width"]
            second_bottom = second_box["y"] + second_box["height"]

            overlap_x = max(first_box["x"], second_box["x"])
            overlap_y = max(first_box["y"], second_box["y"])
            overlap_right = min(first_right, second_right)
            overlap_bottom = min(first_bottom, second_bottom)
            overlap_width = overlap_right - overlap_x
            overlap_height = overlap_bottom - overlap_y

            if overlap_width <= 0 or overlap_height <= 0:
                continue

            overlaps.append(
                {
                    "first": first_id,
                    "second": second_id,
                    "x": _round_ratio(overlap_x),
                    "y": _round_ratio(overlap_y),
                    "width": _round_ratio(overlap_width),
                    "height": _round_ratio(overlap_height),
                }
            )

    return {
        "version": 1,
        "elements": normalized_elements,
        "overlaps": overlaps,
    }


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
        """Render an HTML template to PNG bytes."""
        return self.render_with_layout(
            template_path=template_path,
            variables=variables,
            size=size,
            assets=assets,
        ).png_bytes

    def render_with_layout(
        self,
        template_path: Path,
        variables: Dict[str, str],
        size: Tuple[int, int],
        assets: Optional[Dict[str, str]] = None,
    ) -> HtmlRenderResult:
        """Render an HTML template to PNG bytes.

        Args:
            template_path: Path to the HTML template file
            variables: Dict of {{key}} -> value substitutions
            size: (width, height) viewport size in pixels
            assets: Dict of {relative_name: absolute_path} to symlink into sandbox

        Returns:
            Rendered PNG bytes plus compact layout JSON data
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
            result = self.render_staged_with_layout(index_path.parent, size)

            logger.info(
                f"Rendered HTML template {template_path.name} " f"at {width}x{height}"
            )
            return result

        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def render_staged(self, workspace_dir: Path, size: Tuple[int, int]) -> bytes:
        """Render a pre-staged HTML workspace directory to PNG bytes."""
        return self.render_staged_with_layout(workspace_dir, size).png_bytes

    def render_staged_with_layout(
        self, workspace_dir: Path, size: Tuple[int, int]
    ) -> HtmlRenderResult:
        """Render a pre-staged HTML workspace directory and extract layout data."""
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
            raw_elements = page.evaluate(
                """async () => {
                    if (document.readyState !== "complete") {
                        await new Promise((resolve) => {
                            window.addEventListener("load", resolve, { once: true });
                        });
                    }

                    const stylesheetLinks = Array.from(
                        document.querySelectorAll('link[rel="stylesheet"]')
                    );
                    await Promise.all(
                        stylesheetLinks.map(async (link) => {
                            if (link.sheet) {
                                return;
                            }

                            await new Promise((resolve) => {
                                link.addEventListener("load", resolve, { once: true });
                                link.addEventListener("error", resolve, { once: true });
                            });
                        })
                    );

                    if (document.fonts && document.fonts.ready) {
                        try {
                            await document.fonts.ready;
                        } catch (error) {
                            // Ignore font readiness errors and fall back to current layout.
                        }
                    }

                    const images = Array.from(document.images);
                    await Promise.all(
                        images.map(async (image) => {
                            if (!image.complete) {
                                await new Promise((resolve, reject) => {
                                    image.addEventListener("load", resolve, { once: true });
                                    image.addEventListener("error", reject, { once: true });
                                }).catch(() => undefined);
                            }

                            if (typeof image.decode === "function") {
                                try {
                                    await image.decode();
                                } catch (error) {
                                    // Ignore decode failures and use the current layout.
                                }
                            }
                        })
                    );

                    await new Promise((resolve) => requestAnimationFrame(() => resolve()));

                    return Array.from(document.querySelectorAll("[data-kou-id]"))
                        .map((node) => {
                            const rect = node.getBoundingClientRect();
                            const style = window.getComputedStyle(node);
                            const element = {
                                id: node.getAttribute("data-kou-id"),
                                left: rect.left,
                                top: rect.top,
                                right: rect.right,
                                bottom: rect.bottom,
                            };

                            const role = node.getAttribute("data-kou-role");
                            if (role) {
                                element.role = role;
                            }

                            const text = (node.innerText || "").replace(/\\s+/g, " ").trim();
                            if (text) {
                                element.text = text;
                            }

                            if (node.tagName.toLowerCase() === "img") {
                                const src = node.getAttribute("src");
                                if (src) {
                                    element.src = src;
                                }
                            }

                            if (style.zIndex && style.zIndex !== "auto") {
                                const parsedZIndex = Number(style.zIndex);
                                if (Number.isFinite(parsedZIndex)) {
                                    element.zIndex = parsedZIndex;
                                }
                            }

                            return element;
                        })
                        .filter((element) => Boolean(element.id));
                }"""
            )
            png_bytes = page.screenshot(type="png", full_page=False)
            layout = _build_layout_manifest(raw_elements, size)
            return HtmlRenderResult(png_bytes=png_bytes, layout=layout)
        finally:
            page.close()

    def close(self):
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

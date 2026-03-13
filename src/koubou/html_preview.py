"""Local HTML live preview dashboard with SSE-based hot reload."""

from __future__ import annotations

import html
import json
import logging
import mimetypes
import queue
import shutil
import tempfile
import threading
import webbrowser
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)


@dataclass
class HtmlPreviewSlide:
    """Metadata for a live-previewed slide."""

    screenshot_id: str
    title: str
    aspect_ratio: float
    kind: str
    path: str
    status: str = "ready"
    error: Optional[str] = None


class HtmlPreviewWorkspace:
    """Stable temp workspace for HTML preview slides."""

    def __init__(self) -> None:
        self.root_dir = Path(tempfile.mkdtemp(prefix="koubou_live_preview_"))
        self.slides_dir = self.root_dir / "slides"
        self.slides_dir.mkdir(parents=True, exist_ok=True)

    def stage_slide(
        self,
        *,
        screenshot_id: str,
        builder: Callable[[Path], None],
    ) -> Path:
        temp_dir = self.slides_dir / f".{screenshot_id}.tmp"
        final_dir = self.slides_dir / screenshot_id

        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)
        builder(temp_dir)

        previous_dir = None
        if final_dir.exists():
            previous_dir = self.slides_dir / f".{screenshot_id}.old"
            if previous_dir.exists():
                shutil.rmtree(previous_dir)
            final_dir.replace(previous_dir)

        temp_dir.replace(final_dir)
        if previous_dir and previous_dir.exists():
            shutil.rmtree(previous_dir)

        return final_dir

    def remove_stale_slides(self, valid_screenshot_ids: Iterable[str]) -> None:
        valid = set(valid_screenshot_ids)
        for path in self.slides_dir.iterdir():
            if path.name.startswith("."):
                continue
            if path.name not in valid:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()

    def cleanup(self) -> None:
        shutil.rmtree(self.root_dir, ignore_errors=True)


class _SseBroker:
    def __init__(self) -> None:
        self._subscribers: List[queue.Queue[Optional[str]]] = []
        self._lock = threading.Lock()

    def subscribe(self) -> queue.Queue[Optional[str]]:
        subscriber: queue.Queue[Optional[str]] = queue.Queue()
        with self._lock:
            self._subscribers.append(subscriber)
        return subscriber

    def unsubscribe(self, subscriber: queue.Queue[Optional[str]]) -> None:
        with self._lock:
            if subscriber in self._subscribers:
                self._subscribers.remove(subscriber)

    def publish(self, event: str, payload: Dict[str, object]) -> None:
        message = f"event: {event}\ndata: {json.dumps(payload)}\n\n"
        with self._lock:
            subscribers = list(self._subscribers)
        for subscriber in subscribers:
            subscriber.put(message)

    def close(self) -> None:
        with self._lock:
            subscribers = list(self._subscribers)
            self._subscribers.clear()
        for subscriber in subscribers:
            subscriber.put(None)


class HtmlPreviewServer:
    """Serve the live-preview dashboard and staged slide assets."""

    def __init__(self, workspace: HtmlPreviewWorkspace) -> None:
        self.workspace = workspace
        self._slides: List[HtmlPreviewSlide] = []
        self._broker = _SseBroker()
        self._sequence = 0
        self._server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    @property
    def url(self) -> str:
        assert self._server is not None
        return f"http://127.0.0.1:{self._server.server_port}/"

    def start(self) -> None:
        if self._server is not None:
            return

        server = ThreadingHTTPServer(("127.0.0.1", 0), self._make_handler())
        server.preview_server = self  # type: ignore[attr-defined]
        self._server = server
        self._thread = threading.Thread(
            target=server.serve_forever,
            name="koubou-html-preview",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._broker.close()
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def open_browser(self) -> bool:
        try:
            return bool(webbrowser.open(self.url, new=2))
        except Exception as exc:
            logger.warning("Failed to open browser for HTML preview: %s", exc)
            return False

    def set_slides(self, slides: List[HtmlPreviewSlide]) -> None:
        self._slides = slides

    def publish_reload_slides(self, screenshot_ids: List[str]) -> None:
        if not screenshot_ids:
            return
        self._sequence += 1
        affected = set(screenshot_ids)
        for slide in self._slides:
            if slide.screenshot_id in affected:
                slide.status = "ready"
                slide.error = None
        self._broker.publish(
            "reload-slides",
            {"screenshots": screenshot_ids, "sequence": self._sequence},
        )

    def publish_full_reload(self) -> None:
        self._sequence += 1
        self._broker.publish("full-reload", {"sequence": self._sequence})

    def publish_slide_error(self, screenshot_id: str, error: str) -> None:
        for slide in self._slides:
            if slide.screenshot_id == screenshot_id:
                slide.status = "error"
                slide.error = error
                break
        self._broker.publish(
            "slide-error",
            {"screenshot": screenshot_id, "error": error},
        )

    def _make_handler(self):
        preview_server = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                path = parsed.path
                if path == "/":
                    preview_server._serve_dashboard(self)
                    return
                if path == "/events":
                    preview_server._serve_events(self)
                    return
                if path.startswith("/slides/"):
                    preview_server._serve_slide(self, path, parsed.query)
                    return
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")

            def log_message(self, format: str, *args) -> None:  # noqa: A003
                logger.debug("HTML preview: " + format, *args)

        return Handler

    def _serve_dashboard(self, handler: BaseHTTPRequestHandler) -> None:
        body = self._dashboard_html().encode("utf-8")
        handler.send_response(HTTPStatus.OK)
        handler.send_header("Content-Type", "text/html; charset=utf-8")
        handler.send_header("Cache-Control", "no-store")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)

    def _serve_events(self, handler: BaseHTTPRequestHandler) -> None:
        subscriber = self._broker.subscribe()
        handler.send_response(HTTPStatus.OK)
        handler.send_header("Content-Type", "text/event-stream")
        handler.send_header("Cache-Control", "no-store")
        handler.send_header("Connection", "keep-alive")
        handler.end_headers()
        try:
            handler.wfile.write(b": connected\n\n")
            handler.wfile.flush()
            while True:
                try:
                    message = subscriber.get(timeout=0.5)
                except queue.Empty:
                    handler.wfile.write(b": keepalive\n\n")
                    handler.wfile.flush()
                    continue

                if message is None:
                    break

                handler.wfile.write(message.encode("utf-8"))
                handler.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            self._broker.unsubscribe(subscriber)

    def _serve_slide(
        self, handler: BaseHTTPRequestHandler, path: str, query_string: str
    ) -> None:
        relative = path.removeprefix("/slides/").strip("/")
        if not relative:
            handler.send_error(HTTPStatus.NOT_FOUND, "Missing slide")
            return

        parts = relative.split("/", 1)
        screenshot_id = parts[0]
        asset_path = parts[1] if len(parts) > 1 else "index.html"
        file_path = (self.workspace.slides_dir / screenshot_id / asset_path).resolve()
        slide_root = (self.workspace.slides_dir / screenshot_id).resolve()

        if slide_root not in file_path.parents and file_path != slide_root:
            handler.send_error(HTTPStatus.NOT_FOUND, "Invalid path")
            return
        if not file_path.exists() or not file_path.is_file():
            handler.send_error(HTTPStatus.NOT_FOUND, "Slide asset not found")
            return

        content_type = (
            "text/html; charset=utf-8"
            if file_path.name == "index.html"
            else mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        )
        data = file_path.read_bytes()

        handler.send_response(HTTPStatus.OK)
        handler.send_header("Content-Type", content_type)
        cache_control = (
            "no-store" if parse_qs(query_string).get("v") else "public, max-age=60"
        )
        handler.send_header("Cache-Control", cache_control)
        handler.send_header("Content-Length", str(len(data)))
        handler.end_headers()
        handler.wfile.write(data)

    def _dashboard_html(self) -> str:
        cards = []
        for slide in self._slides:
            title = html.escape(slide.title)
            screenshot_id = html.escape(slide.screenshot_id)
            status = html.escape(slide.status)
            ratio = slide.aspect_ratio if slide.aspect_ratio > 0 else 0.46
            error = html.escape(slide.error or "")
            cards.append(
                f"""
                {self._render_slide_card(
                    screenshot_id=screenshot_id,
                    title=title,
                    status=status,
                    ratio=ratio,
                    error=error,
                    kind=slide.kind,
                    path=html.escape(slide.path),
                )}
                """
            )

        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Koubou Live Preview</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
      background: #0c1023;
      color: #f6f7fb;
      padding: 24px;
    }}
    h1 {{
      font-size: 28px;
      margin: 0 0 6px;
    }}
    p {{
      margin: 0 0 24px;
      color: rgba(246, 247, 251, 0.72);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 420px));
      gap: 20px;
      align-items: start;
      justify-content: center;
    }}
    .card {{
      width: 100%;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 18px;
      padding: 14px;
      backdrop-filter: blur(16px);
    }}
    .card-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
    }}
    .status {{
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.08);
      color: rgba(255, 255, 255, 0.72);
    }}
    .status-updating {{ background: rgba(251, 191, 36, 0.14); color: #fbbf24; }}
    .status-error {{ background: rgba(248, 113, 113, 0.14); color: #f87171; }}
    .status-ready {{ background: rgba(74, 222, 128, 0.14); color: #4ade80; }}
    .frame-shell {{
      position: relative;
      width: 100%;
      aspect-ratio: var(--aspect);
      border-radius: 14px;
      overflow: hidden;
      background: #04060d;
      border: 1px solid rgba(255, 255, 255, 0.06);
    }}
    iframe,
    img {{
      width: 100%;
      height: 100%;
      border: 0;
      background: white;
      display: block;
      object-fit: contain;
    }}
    .error-banner {{
      position: absolute;
      left: 12px;
      right: 12px;
      bottom: 12px;
      display: none;
      background: rgba(15, 16, 25, 0.82);
      color: #ffd5d5;
      border: 1px solid rgba(248, 113, 113, 0.35);
      border-radius: 10px;
      padding: 10px 12px;
      font-size: 13px;
    }}
    .error-banner.visible {{ display: block; }}
  </style>
</head>
<body>
  <h1>Koubou Live Preview</h1>
  <p>Hot reload is active for screenshots in the current config.</p>
  <section class="grid">
    {''.join(cards)}
  </section>
  <script>
    const cards = new Map(
      [...document.querySelectorAll('[data-slide]')].map((el) => [el.dataset.slide, el])
    );
    let lastSequence = 0;

    function setStatus(slideId, status, errorText = '') {{
      const card = cards.get(slideId);
      if (!card) return;
      const statusEl = card.querySelector('[data-status]');
      const errorEl = card.querySelector('[data-error]');
      statusEl.textContent = status;
      statusEl.className = `status status-${{status}}`;
      if (errorText) {{
        errorEl.textContent = errorText;
        errorEl.classList.add('visible');
      }} else {{
        errorEl.textContent = '';
        errorEl.classList.remove('visible');
      }}
    }}

    function reloadFrame(slideId, sequence) {{
      const card = cards.get(slideId);
      if (!card) return;
      const media = card.querySelector('[data-frame], [data-image]');
      if (!media) return;
      setStatus(slideId, 'updating');
      const url = new URL(media.getAttribute('src'), window.location.origin);
      url.searchParams.set('v', sequence);
      media.onload = () => setStatus(slideId, 'ready');
      media.src = url.toString();
    }}

    const source = new EventSource('/events');
    source.addEventListener('reload-slides', (event) => {{
      const payload = JSON.parse(event.data);
      lastSequence = payload.sequence || (lastSequence + 1);
      for (const slideId of payload.screenshots || []) {{
        reloadFrame(slideId, lastSequence);
      }}
    }});
    source.addEventListener('full-reload', () => window.location.reload());
    source.addEventListener('slide-error', (event) => {{
      const payload = JSON.parse(event.data);
      setStatus(payload.screenshot, 'error', payload.error || 'Preview update failed');
    }});
  </script>
</body>
</html>"""

    def _render_slide_card(
        self,
        *,
        screenshot_id: str,
        title: str,
        status: str,
        ratio: float,
        error: str,
        kind: str,
        path: str,
    ) -> str:
        if kind == "image":
            media = f'<img data-image src="{path}" alt="{title}" loading="eager">'
        else:
            media = (
                f'<iframe data-frame src="{path}" loading="eager" '
                f'referrerpolicy="no-referrer"></iframe>'
            )

        return f"""
        <article class="card" data-slide="{screenshot_id}">
          <header class="card-header">
            <strong>{title}</strong>
            <span class="status status-{status}" data-status>{status}</span>
          </header>
          <div class="frame-shell" style="--aspect:{ratio};">
            {media}
            <div class="error-banner" data-error>{error}</div>
          </div>
        </article>
        """

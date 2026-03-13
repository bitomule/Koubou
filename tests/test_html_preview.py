"""Tests for the HTML live preview dashboard."""

import json
import urllib.request

from PIL import Image

from koubou.html_preview import (
    HtmlPreviewServer,
    HtmlPreviewSlide,
    HtmlPreviewWorkspace,
)
from koubou.renderers.html_staging import stage_html_workspace


class TestHtmlPreviewServer:
    def test_dashboard_and_slide_routes(self):
        workspace = HtmlPreviewWorkspace()
        try:
            workspace.stage_slide(
                screenshot_id="hero",
                builder=lambda stage_dir: (stage_dir / "index.html").write_text(
                    "<html><body>Hello hero</body></html>", encoding="utf-8"
                ),
            )

            server = HtmlPreviewServer(workspace)
            server.set_slides(
                [
                    HtmlPreviewSlide(
                        "hero",
                        "hero",
                        aspect_ratio=1320 / 2868,
                        kind="html",
                        path="/slides/hero/",
                    )
                ]
            )
            server.start()

            with urllib.request.urlopen(server.url, timeout=5) as response:
                assert response.status == 200
                assert "text/html" in response.headers["Content-Type"]
                body = response.read().decode("utf-8")
                assert "Koubou Live Preview" in body
                assert 'data-slide="hero"' in body

            with urllib.request.urlopen(
                f"{server.url}slides/hero/", timeout=5
            ) as response:
                assert response.status == 200
                assert "text/html" in response.headers["Content-Type"]
                assert "Hello hero" in response.read().decode("utf-8")

            server.stop()
        finally:
            workspace.cleanup()

    def test_stage_preserves_generated_assets_inside_workspace(self, tmp_path):
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template = template_dir / "hero.html"
        template.write_text(
            '<html><body><img src="screen.png"></body></html>',
            encoding="utf-8",
        )

        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        generated_asset = workspace_dir / "screen.png"
        Image.new("RGBA", (20, 40), "#ff0000").save(generated_asset)

        stage_html_workspace(
            template_path=template,
            variables={},
            destination_dir=workspace_dir,
            assets={"screen.png": str(generated_asset)},
        )

        assert generated_asset.exists()
        assert (workspace_dir / "index.html").exists()

    def test_events_stream_emits_reload_events(self):
        workspace = HtmlPreviewWorkspace()
        try:
            workspace.stage_slide(
                screenshot_id="hero",
                builder=lambda stage_dir: (stage_dir / "index.html").write_text(
                    "<html><body>Hello hero</body></html>", encoding="utf-8"
                ),
            )

            server = HtmlPreviewServer(workspace)
            server.set_slides(
                [
                    HtmlPreviewSlide(
                        "hero",
                        "hero",
                        aspect_ratio=1320 / 2868,
                        kind="html",
                        path="/slides/hero/",
                    )
                ]
            )
            server.start()

            with urllib.request.urlopen(f"{server.url}events", timeout=5) as response:
                assert response.status == 200
                assert response.headers["Content-Type"] == "text/event-stream"
                response.readline()  # : connected
                response.readline()  # blank separator

                server.publish_reload_slides(["hero"])
                event_line = response.readline().decode("utf-8").strip()
                data_line = response.readline().decode("utf-8").strip()

                assert event_line == "event: reload-slides"
                payload = json.loads(data_line.removeprefix("data: "))
                assert payload["screenshots"] == ["hero"]

            server.stop()
        finally:
            workspace.cleanup()

    def test_dashboard_and_image_routes(self):
        workspace = HtmlPreviewWorkspace()
        try:
            workspace.stage_slide(
                screenshot_id="welcome",
                builder=lambda stage_dir: Image.new("RGB", (40, 80), "#ff0000").save(
                    stage_dir / "preview.png"
                ),
            )

            server = HtmlPreviewServer(workspace)
            server.set_slides(
                [
                    HtmlPreviewSlide(
                        "welcome",
                        "welcome",
                        aspect_ratio=1320 / 2868,
                        kind="image",
                        path="/slides/welcome/preview.png",
                    )
                ]
            )
            server.start()

            with urllib.request.urlopen(server.url, timeout=5) as response:
                body = response.read().decode("utf-8")
                assert 'data-image src="/slides/welcome/preview.png"' in body

            with urllib.request.urlopen(
                f"{server.url}slides/welcome/preview.png", timeout=5
            ) as response:
                assert response.status == 200
                assert response.headers["Content-Type"] == "image/png"

            server.stop()
        finally:
            workspace.cleanup()

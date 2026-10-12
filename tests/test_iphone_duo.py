"""iPhone Duo: bundled frames, App Store sizes and two-display projects."""

import json
from pathlib import Path

import pytest
import yaml
from PIL import Image
from typer.testing import CliRunner

from koubou.cli import _classify_canvas, app
from koubou.config import ProjectConfig, resolve_output_size
from koubou.live_generator import LiveScreenshotGenerator
from koubou.renderers.device_frame import DeviceFrameRenderer

FRAMES_DIR = Path(__file__).resolve().parents[1] / "src" / "koubou" / "frames"
COLORS = ["Night Sky", "Star White"]
POSES = {
    "Inner Open Landscape": ("inner", (3093, 2247), (120, 120, 2853, 2007)),
    "Inner Open Portrait": ("inner", (2247, 3093), (120, 120, 2007, 2853)),
    "Outer Closed Landscape": ("outer", (2194, 1574), (80, 88, 2034, 1398)),
    "Outer Closed Portrait": ("outer", (1574, 2194), (88, 80, 1398, 2034)),
    "Outer Open": ("outer", (3056, 2194), (1570, 80, 1398, 2034)),
}
OUTER = "iPhone Duo - Night Sky - Outer Closed Portrait"
INNER = "iPhone Duo - Night Sky - Inner Open Portrait"


@pytest.fixture(scope="module")
def renderer():
    return DeviceFrameRenderer(FRAMES_DIR)


@pytest.fixture
def project_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "koubou.frame_manager.ensure_frames", lambda verbose=False: FRAMES_DIR
    )
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _project(tmp_path: Path, **overrides) -> dict:
    data = {
        "project": {
            "name": "Duo",
            "output_dir": str(tmp_path / "output"),
            "displays": {
                "outer": {"device": OUTER, "output_size": "iPhoneDuo_Outer"},
                "inner": {"device": INNER, "output_size": "iPhoneDuo_Inner"},
            },
        },
        "screenshots": {
            "hero": {
                "template": "templates/outer.html",
                "variables": {"headline": "Clean up", "subtitle": "Fast"},
                "assets": {"app_screenshot": "raw/outer/hero.png"},
                "displays": {
                    "inner": {
                        "template": "templates/inner.html",
                        "variables": {"subtitle": "Side by side"},
                        "assets": {"app_screenshot": "raw/inner/hero.png"},
                    }
                },
            }
        },
    }
    data["project"].update(overrides)
    return data


@pytest.mark.parametrize(
    "name,size",
    [
        ("iPhoneDuo_Outer", (1398, 2034)),
        ("iPhoneDuo_Outer_Landscape", (2034, 1398)),
        ("iPhoneDuo_Inner", (2007, 2853)),
        ("iPhoneDuo_Inner_Landscape", (2853, 2007)),
    ],
)
def test_named_sizes_match_app_store_connect(name, size):
    assert resolve_output_size(name) == size


@pytest.mark.parametrize("color", COLORS)
@pytest.mark.parametrize("pose", POSES)
def test_every_duo_frame_is_bundled_with_metadata(renderer, color, pose):
    name = f"iPhone Duo - {color} - {pose}"
    display, frame_size, (x, y, width, height) = POSES[pose]

    assert renderer.get_frame_size(name) == frame_size
    info = renderer._get_frame_info(name)
    assert info is not None
    assert info["display"] == display
    assert info["appstore_device_type"] == "IPHONE_DUO"
    assert info["screen_bounds"] == {"x": x, "y": y, "width": width, "height": height}


@pytest.mark.parametrize("name", ["iPhone Duo - Night Sky - Outer Open", INNER, OUTER])
def test_calibration_matches_transparent_screen(renderer, name):
    inspection = renderer.inspect_frame(name)
    bbox = inspection["screen_bbox"]
    bounds = inspection["screen_bounds"]

    assert (bbox["left"], bbox["top"], bbox["width"], bbox["height"]) == (
        bounds["x"],
        bounds["y"],
        bounds["width"],
        bounds["height"],
    )


def test_outer_camera_cutout_stays_masked(renderer):
    frame = Image.open(FRAMES_DIR / f"{OUTER}.png").convert("RGBA")
    mask = renderer.generate_screen_mask_from_image(frame)
    width, height = frame.size

    assert mask.getpixel((width // 2, height // 2)) == 255
    camera = [
        (x, y)
        for x in range(width - 300, width)
        for y in range(0, 300)
        if frame.getpixel((x, y))[3] == 255 and mask.getpixel((x, y)) == 0
    ]
    inside_screen = [(x, y) for x, y in camera if 88 < x < 1486 and 80 < y < 2114]
    assert inside_screen, "the camera hole inside the outer screen must be masked"


def test_inner_display_has_no_seam_at_the_fold(renderer):
    frame = Image.open(FRAMES_DIR / f"{INNER}.png").convert("RGBA")
    mask = renderer.generate_screen_mask_from_image(frame)
    fold_y = frame.height // 2

    row = [mask.getpixel((x, fold_y)) for x in range(130, frame.width - 130)]
    assert min(row) == 255


def test_displays_project_resolves_each_display(tmp_path):
    config = ProjectConfig(**_project(tmp_path))
    displays = config.project.resolved_displays()

    assert [(d.name, d.device, d.output_size) for d in displays] == [
        ("outer", OUTER, (1398, 2034)),
        ("inner", INNER, (2007, 2853)),
    ]


def test_display_override_merges_variables_and_assets(tmp_path):
    config = ProjectConfig(**_project(tmp_path))

    outer = config.screenshots_for_display("outer")["hero"]
    inner = config.screenshots_for_display("inner")["hero"]

    assert outer.template == "templates/outer.html"
    assert outer.variables == {"headline": "Clean up", "subtitle": "Fast"}
    assert inner.template == "templates/inner.html"
    assert inner.variables == {"headline": "Clean up", "subtitle": "Side by side"}
    assert inner.assets == {"app_screenshot": "raw/inner/hero.png"}
    assert inner.displays == {}


def test_single_device_projects_are_unchanged(tmp_path):
    config = ProjectConfig(
        project={
            "name": "Classic",
            "output_dir": str(tmp_path / "output"),
            "device": "iPhone 17 Pro - Silver - Portrait",
            "output_size": "iPhone6_3",
        },
        screenshots={"one": {"template": "t.html"}},
    )

    [display] = config.project.resolved_displays()
    assert (display.name, display.device, display.output_size) == (
        None,
        "iPhone 17 Pro - Silver - Portrait",
        (1206, 2622),
    )


@pytest.mark.parametrize(
    "project_overrides,message",
    [
        ({"device": OUTER}, "not both"),
        ({"output_size": "iPhoneDuo_Outer"}, "not both"),
        ({"displays": {}}, "project.device is required"),
        (
            {
                "displays": {
                    "a": {"device": OUTER, "output_size": "iPhoneDuo_Outer"},
                    "b": {"device": OUTER, "output_size": "iPhoneDuo_Outer"},
                }
            },
            "its own device frame",
        ),
        (
            {"displays": {"outer": {"device": OUTER, "output_size": "iPhone99"}}},
            "Unknown App Store size",
        ),
    ],
)
def test_invalid_display_projects_are_rejected(tmp_path, project_overrides, message):
    data = _project(tmp_path, **project_overrides)
    data["screenshots"]["hero"].pop("displays")

    with pytest.raises(ValueError, match=message):
        ProjectConfig(**data)


def test_override_for_undeclared_display_is_rejected(tmp_path):
    data = _project(tmp_path)
    data["screenshots"]["hero"]["displays"]["middle"] = {"template": "x.html"}

    with pytest.raises(ValueError, match="unknown display"):
        ProjectConfig(**data)


@pytest.mark.parametrize(
    "device,size,expected",
    [
        (OUTER, (1398, 2034), "duo_outer_portrait"),
        (INNER, (2007, 2853), "duo_inner_portrait"),
        ("iPhone Duo - Night Sky - Inner Open Landscape", (2853, 2007), "landscape"),
        ("iPhone 17 Pro - Silver - Portrait", (1206, 2622), "tall_iphone_portrait"),
    ],
)
def test_canvas_class(device, size, expected):
    assert _classify_canvas(device, size) == expected


def _write_content_project(tmp_path: Path) -> Path:
    (tmp_path / "raw").mkdir()
    Image.new("RGB", (1398, 2034), "#3366cc").save(tmp_path / "raw" / "outer.png")
    Image.new("RGB", (2007, 2853), "#cc6633").save(tmp_path / "raw" / "inner.png")

    def image(asset: str) -> dict:
        return {
            "type": "image",
            "asset": asset,
            "position": ["50%", "55%"],
            "scale": 0.7,
            "frame": True,
        }

    data = {
        "project": {
            "name": "Duo",
            "output_dir": "output",
            "displays": {
                "outer": {"device": OUTER, "output_size": "iPhoneDuo_Outer"},
                "inner": {"device": INNER, "output_size": "iPhoneDuo_Inner"},
            },
        },
        "defaults": {"background": {"type": "solid", "colors": ["#f4f1ea"]}},
        "screenshots": {
            "hero": {
                "content": [image("raw/outer.png")],
                "displays": {"inner": {"content": [image("raw/inner.png")]}},
            }
        },
    }
    config_file = tmp_path / "duo.yaml"
    config_file.write_text(yaml.safe_dump(data, sort_keys=False))
    return config_file


def test_generate_renders_both_displays(project_dir):
    tmp_path = project_dir
    config_file = _write_content_project(tmp_path)

    result = CliRunner().invoke(app, ["generate", str(config_file), "--output", "json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert [item["name"] for item in payload] == ["outer/hero", "inner/hero"]
    outer = Image.open(tmp_path / "output" / OUTER.replace(" ", "_") / "hero.png")
    inner = Image.open(tmp_path / "output" / INNER.replace(" ", "_") / "hero.png")
    assert outer.size == (1398, 2034)
    assert inner.size == (2007, 2853)
    assert inner.getpixel((1003, 1500))[:3] == (204, 102, 51)
    assert outer.getpixel((699, 1100))[:3] == (51, 102, 204)


def test_live_preview_has_a_slide_per_display(project_dir):
    tmp_path = project_dir
    config_file = _write_content_project(tmp_path)
    live = LiveScreenshotGenerator(config_file)
    live.current_config = live.load_config()
    try:
        slides = live.get_preview_slides()

        assert [s.screenshot_id for s in slides] == ["hero@outer", "hero@inner"]
        assert [s.title for s in slides] == ["hero · outer", "hero · inner"]
        assert slides[0].aspect_ratio == pytest.approx(1398 / 2034)
        assert slides[1].aspect_ratio == pytest.approx(2007 / 2853)
        assert slides[1].path == "/slides/hero@inner/preview.png"
        assert live.preview_slide_ids_for("hero") == ["hero@outer", "hero@inner"]

        inner_dir = tmp_path / "output" / INNER.replace(" ", "_")
        inner_dir.mkdir(parents=True)
        Image.new("RGB", (2007, 2853), "blue").save(inner_dir / "hero.png")
        errors = live.sync_preview_workspace({"hero@inner"})

        assert errors == {}
        staged = live.preview_workspace.slides_dir / "hero@inner" / "preview.png"
        assert staged.exists()
    finally:
        live.close()

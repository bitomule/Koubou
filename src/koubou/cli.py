"""Command line interface for Koubou."""

import json
import logging
import signal
from pathlib import Path
from typing import Any, Optional, Set, Tuple

import typer
import yaml
from PIL import Image, ImageDraw
from rich.console import Console
from rich.live import Live
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .config import ProjectConfig, resolve_output_size
from .exceptions import KoubouError
from .generator import ScreenshotGenerator
from .html_preview import HtmlPreviewServer
from .html_setup import (
    check_html_environment,
    format_html_environment_error,
    setup_html_environment,
)
from .live_generator import LiveScreenshotGenerator
from .watcher import LiveWatcher

app = typer.Typer(
    name="kou",
    help="Koubou - The artisan workshop for App Store screenshots",
    add_completion=False,
)
console = Console()


def setup_logging(verbose: bool = False, log_console: Console = None) -> None:
    log_level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=log_console or console, show_path=False)],
    )


def _create_config_file(output_file: Path, name: str, force: bool = False) -> None:
    _create_config_file_with_mode(
        output_file,
        name,
        mode="content",
        force=force,
    )


def _create_config_file_with_mode(
    output_file: Path,
    name: str,
    *,
    mode: str,
    force: bool = False,
) -> None:
    if output_file.exists() and not force:
        console.print(
            f"File {output_file} already exists. Use --force to overwrite.",
            style="red",
        )
        raise typer.Exit(1)

    normalized_mode = mode.strip().lower()
    if normalized_mode not in {"content", "html"}:
        console.print(
            f"Unsupported create-config mode: {mode}. Use 'content' or 'html'.",
            style="red",
        )
        raise typer.Exit(1)

    if normalized_mode == "html":
        sample_config = _build_html_sample_config(name)
    else:
        sample_config = _build_content_sample_config(name)

    with open(output_file, "w") as f:
        yaml.dump(sample_config, f, default_flow_style=False, indent=2)

    _create_sample_assets(output_file.parent, force=force)
    if normalized_mode == "html":
        _create_sample_html_templates(output_file.parent, force=force)

    console.print(
        f"Created {normalized_mode} sample configuration: {output_file}",
        style="green",
    )
    console.print(
        f"Created sample assets: {output_file.parent / 'screenshots'}",
        style="green",
    )
    if normalized_mode == "html":
        console.print(
            f"Created sample templates: {output_file.parent / 'templates'}",
            style="green",
        )
    console.print("\nEdit the configuration file and run:", style="blue")
    if normalized_mode == "html":
        console.print(f"   kou generate {output_file} --setup-html", style="cyan")
    else:
        console.print(f"   kou generate {output_file}", style="cyan")


def _build_content_sample_config(name: str) -> dict[str, Any]:
    return {
        "project": {
            "name": name,
            "output_dir": "Screenshots/Generated",
            "device": "iPhone 16 Pro - Black Titanium - Portrait",
            "output_size": "iPhone6_9",
        },
        "defaults": {
            "background": {
                "type": "linear",
                "colors": ["#E8F0FE", "#F8FBFF"],
                "direction": 180,
            }
        },
        "screenshots": {
            "welcome_screen": {
                "content": [
                    {
                        "type": "text",
                        "content": "Beautiful App",
                        "position": ["50%", "15%"],
                        "size": 48,
                        "color": "#8E4EC6",
                        "weight": "bold",
                    },
                    {
                        "type": "text",
                        "content": "Transform your workflow today",
                        "position": ["50%", "25%"],
                        "size": 24,
                        "color": "#1A73E8",
                    },
                    {
                        "type": "image",
                        "asset": "screenshots/home.png",
                        "position": ["50%", "60%"],
                        "scale": 0.6,
                        "frame": True,
                    },
                ],
            },
            "features_screen": {
                "content": [
                    {
                        "type": "text",
                        "content": "Amazing Features",
                        "position": ["50%", "10%"],
                        "size": 42,
                        "color": "#8E4EC6",
                        "weight": "bold",
                    },
                    {
                        "type": "image",
                        "asset": "screenshots/features.png",
                        "position": ["50%", "65%"],
                        "scale": 0.5,
                        "frame": True,
                    },
                ],
            },
            "gradient_showcase": {
                "content": [
                    {
                        "type": "text",
                        "content": "Gradient Magic",
                        "position": ["50%", "15%"],
                        "size": 48,
                        "gradient": {
                            "type": "linear",
                            "colors": ["#FF6B6B", "#4ECDC4", "#45B7D1"],
                            "direction": 45,
                        },
                        "weight": "bold",
                    },
                    {
                        "type": "text",
                        "content": "Beautiful gradients for stunning text",
                        "position": ["50%", "25%"],
                        "size": 24,
                        "gradient": {
                            "type": "radial",
                            "colors": ["#667eea", "#764ba2"],
                            "center": ["50%", "50%"],
                            "radius": "70%",
                        },
                    },
                    {
                        "type": "text",
                        "content": "Advanced Color Control",
                        "position": ["50%", "35%"],
                        "size": 28,
                        "gradient": {
                            "type": "linear",
                            "colors": ["#f093fb", "#f5576c", "#4facfe"],
                            "positions": [0.0, 0.3, 1.0],
                            "direction": 90,
                        },
                        "stroke_width": 2,
                        "stroke_color": "#333333",
                    },
                    {
                        "type": "image",
                        "asset": "screenshots/gradient_demo.png",
                        "position": ["50%", "70%"],
                        "scale": 0.5,
                        "frame": True,
                    },
                ],
            },
        },
    }


def _build_html_sample_config(name: str) -> dict[str, Any]:
    return {
        "project": {
            "name": name,
            "output_dir": "Screenshots/Generated",
            "device": "iPhone 16 Pro - Black Titanium - Portrait",
            "output_size": "iPhone6_9",
        },
        "screenshots": {
            "hero": {
                "template": "templates/hero.html",
                "variables": {
                    "headline": "Beautiful App",
                    "subtitle": "Launch polished App Store screenshots fast",
                },
                "assets": {
                    "screen": "screenshots/home.png",
                },
            },
            "feature": {
                "template": "templates/feature.html",
                "variables": {
                    "headline": "Showcase Features",
                    "subtitle": "Use HTML when you need more layout control",
                },
                "assets": {
                    "screen": "screenshots/features.png",
                },
            },
            "closing": {
                "template": "templates/closing.html",
                "frame": False,
                "variables": {
                    "headline": "Ship Faster",
                    "subtitle": "Templates, localization, live preview",
                },
            },
        },
    }


def _create_sample_assets(base_dir: Path, force: bool = False) -> None:
    screenshots_dir = base_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    _write_sample_image(
        screenshots_dir / "home.png",
        background="#f5f7ff",
        accent="#4f46e5",
        title="Home",
        subtitle="Your workflow at a glance",
        force=force,
    )
    _write_sample_image(
        screenshots_dir / "features.png",
        background="#eefbf6",
        accent="#0f766e",
        title="Features",
        subtitle="Everything organized beautifully",
        force=force,
    )
    _write_sample_image(
        screenshots_dir / "gradient_demo.png",
        background="#fff7ed",
        accent="#ea580c",
        title="Gradient Demo",
        subtitle="Visual polish for your next launch",
        force=force,
    )


def _write_sample_image(
    path: Path,
    *,
    background: str,
    accent: str,
    title: str,
    subtitle: str,
    force: bool,
) -> None:
    if path.exists() and not force:
        return

    image = Image.new("RGB", (1290, 2796), background)
    draw = ImageDraw.Draw(image)

    card_bounds = (105, 180, 1185, 2616)
    draw.rounded_rectangle(card_bounds, radius=110, fill="white")
    draw.rounded_rectangle((165, 280, 1125, 520), radius=72, fill=accent)
    draw.rounded_rectangle((165, 620, 1125, 1735), radius=84, fill="#f8fafc")
    draw.rounded_rectangle((165, 1845, 1125, 2440), radius=84, fill="#f8fafc")

    draw.text((230, 345), title, fill="white")
    draw.text((230, 430), subtitle, fill="#e0e7ff")

    for index in range(4):
        top = 760 + index * 210
        draw.rounded_rectangle(
            (230, top, 1060, top + 130),
            radius=36,
            fill="white",
            outline="#dbe4ff",
            width=6,
        )
        draw.text((275, top + 38), f"Sample row {index + 1}", fill="#111827")
        draw.rounded_rectangle(
            (925, top + 34, 1030, top + 96),
            radius=28,
            fill=accent,
        )

    draw.text((230, 1925), "Highlights", fill="#111827")
    draw.text(
        (230, 2015), "Cards, gradients, and frames ready to tweak.", fill="#6b7280"
    )
    draw.rounded_rectangle((230, 2125, 1060, 2340), radius=48, fill=accent)
    draw.text((290, 2200), "Drop in your own screenshots here", fill="white")

    image.save(path)


def _create_sample_html_templates(base_dir: Path, force: bool = False) -> None:
    templates_dir = base_dir / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    template_files = {
        "styles.css": """* { box-sizing: border-box; }
body {
  margin: 0;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
}
.page {
  position: relative;
  width: 100%;
  height: 100%;
  color: white;
}
.hero-page {
  background: linear-gradient(180deg, #0b1020 0%, #1b1f3b 100%);
}
.feature-page {
  background: linear-gradient(180deg, #fff7ed 0%, #ffedd5 100%);
  color: #111827;
}
.closing-page {
  background: linear-gradient(180deg, #111827 0%, #1f2937 100%);
}
.copy {
  position: absolute;
  left: 7%;
  right: 7%;
  top: 8%;
  z-index: 2;
}
.copy h1 {
  margin: 0;
  font-size: 10vw;
  line-height: 0.95;
  letter-spacing: -0.05em;
}
.copy p {
  margin: 2.5vh 0 0;
  font-size: 3.9vw;
  line-height: 1.25;
  opacity: 0.8;
}
.device {
  position: absolute;
  left: 50%;
  bottom: 4%;
  transform: translateX(-50%);
  width: 72vw;
  filter: drop-shadow(0 40px 80px rgba(0, 0, 0, 0.32));
}
.feature-layout .copy {
  top: 10%;
  right: 44%;
}
.feature-layout .device {
  left: auto;
  right: -3%;
  bottom: 8%;
  transform: rotate(-7deg);
  width: 60vw;
}
.closing-stack {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 3.5vh;
  padding: 10%;
  text-align: center;
}
.closing-stack h1 {
  margin: 0;
  font-size: 12vw;
  line-height: 0.92;
  letter-spacing: -0.06em;
}
.closing-stack p {
  margin: 0;
  font-size: 4.2vw;
  line-height: 1.3;
  max-width: 80%;
  opacity: 0.82;
}
""",
        "hero.html": """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="styles.css">
</head>
<body class="page hero-page">
  <div class="copy">
    <h1>{{headline}}</h1>
    <p>{{subtitle}}</p>
  </div>
  <img class="device" src="{{screen}}" alt="">
</body>
</html>
""",
        "feature.html": """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="styles.css">
</head>
<body class="page feature-page feature-layout">
  <div class="copy">
    <h1>{{headline}}</h1>
    <p>{{subtitle}}</p>
  </div>
  <img class="device" src="{{screen}}" alt="">
</body>
</html>
""",
        "closing.html": """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="styles.css">
</head>
<body class="page closing-page">
  <div class="closing-stack">
    <h1>{{headline}}</h1>
    <p>{{subtitle}}</p>
  </div>
</body>
</html>
""",
    }

    for filename, content in template_files.items():
        path = templates_dir / filename
        if path.exists() and not force:
            continue
        path.write_text(content, encoding="utf-8")


def _show_results(results, output_dir: str) -> None:
    table = Table(
        title="Generation Results", show_header=True, header_style="bold magenta"
    )
    table.add_column("Screenshot", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Output Path", style="blue")

    for name, path, success, error in results:
        if success:
            status = "Success"
            output_path = str(path) if path else ""
        else:
            status = "Failed"
            output_path = (
                error[:50] + "..." if error and len(error) > 50 else (error or "")
            )

        table.add_row(name, status, output_path)

    console.print(table)
    console.print(f"\nOutput directory: {Path(output_dir).absolute()}", style="blue")


def _project_uses_html_templates(project_config: ProjectConfig) -> bool:
    return any(
        screenshot_def.template
        for screenshot_def in project_config.screenshots.values()
    )


def _prepare_html_environment(
    *,
    setup_requested: bool,
    verbose: bool,
    output_console: Console,
) -> None:
    if setup_requested:
        status = setup_html_environment(verbose=verbose)
        if status.did_install_browser:
            output_console.print(
                f"HTML ready: installed {status.browser_name}", style="green"
            )
        else:
            output_console.print(
                f"HTML ready: using {status.browser_name}", style="green"
            )
        return

    status = check_html_environment()
    if not status.ready:
        raise KoubouError(format_html_environment_error(status))


def _parse_output_size_option(value: str) -> Tuple[int, int]:
    raw = value.strip()

    try:
        return resolve_output_size(raw)
    except ValueError:
        pass

    if "x" in raw.lower():
        width_str, height_str = raw.lower().split("x", 1)
        try:
            return (int(width_str.strip()), int(height_str.strip()))
        except ValueError as exc:
            raise typer.BadParameter(
                "Custom output sizes must look like 1320x2868 or [1320, 2868]"
            ) from exc

    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise typer.BadParameter(
                "Custom output sizes must look like 1320x2868 or [1320, 2868]"
            ) from exc
        if (
            isinstance(parsed, list)
            and len(parsed) == 2
            and all(isinstance(item, int) for item in parsed)
        ):
            return (parsed[0], parsed[1])

    if "," in raw:
        width_str, height_str = raw.split(",", 1)
        try:
            return (int(width_str.strip()), int(height_str.strip()))
        except ValueError as exc:
            raise typer.BadParameter(
                "Custom output sizes must look like 1320x2868 or [1320, 2868]"
            ) from exc

    raise typer.BadParameter(
        f"Unknown output size '{value}'. Use a named size like iPhone6_9 or "
        "a custom size like 1320x2868."
    )


def _classify_canvas(device: str, output_size: Tuple[int, int]) -> str:
    width, height = output_size
    device_lower = device.lower()

    if "mac" in device_lower:
        return "desktop_like"
    if "watch" in device_lower:
        return "watch_portrait" if height >= width else "landscape"
    if width > height:
        return "landscape"
    if "ipad" in device_lower:
        return "ipad_portrait"
    if "iphone" in device_lower:
        aspect_ratio = height / width
        if aspect_ratio >= 2.1:
            return "tall_iphone_portrait"
        return "short_iphone_portrait"
    return "portrait_generic"


def _frame_inspection_payload(
    *,
    device: str,
    output_size: Tuple[int, int],
    inspection: dict[str, Any],
) -> dict[str, Any]:
    width, height = output_size
    orientation = "landscape" if width > height else "portrait"

    return {
        "device": device,
        "output_size": {"width": width, "height": height},
        "frame_size": inspection["frame_size"],
        "screen_bounds": inspection["screen_bounds"],
        "screen_bbox": inspection["screen_bbox"],
        "screen_ratio": inspection["screen_ratio"],
        "frame_ratio": inspection["frame_ratio"],
        "screen_coverage_ratio": inspection["screen_coverage_ratio"],
        "safe_margins": inspection["safe_margins"],
        "orientation": orientation,
        "canvas_class": _classify_canvas(device, output_size),
    }


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    create_config: Optional[Path] = typer.Option(
        None, "--create-config", help="Create a sample configuration file"
    ),
    name: str = typer.Option(
        "My Screenshot Project",
        "--name",
        help="Project name for config creation",
    ),
    mode: str = typer.Option(
        "content",
        "--mode",
        help="Sample config mode for --create-config: content or html",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        help="Show version and exit",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing files without confirmation",
    ),
):
    """Koubou - The artisan workshop for App Store screenshots"""

    if version:
        from koubou import __version__

        console.print(f"Koubou v{__version__}", style="green")
        raise typer.Exit()

    if create_config:
        _create_config_file_with_mode(create_config, name, mode=mode, force=force)
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()


@app.command()
def generate(
    config_file: Path = typer.Argument(..., help="YAML configuration file"),
    output: str = typer.Option(
        "table", "--output", help="Output format: table or json"
    ),
    setup_html: bool = typer.Option(
        False,
        "--setup-html",
        help="Prepare HTML rendering before generating HTML template screenshots",
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
):
    """Generate screenshots from YAML configuration file"""

    json_mode = output == "json"
    stderr_console = Console(stderr=True) if json_mode else console

    setup_logging(verbose)

    try:
        if not config_file.exists():
            stderr_console.print(
                f"Configuration file not found: {config_file}", style="red"
            )
            raise typer.Exit(1)

        with open(config_file) as f:
            config_data = yaml.safe_load(f)

        try:
            project_config = ProjectConfig(**config_data)
            stderr_console.print("Using flexible content-based API", style="blue")
        except Exception as _e:
            stderr_console.print(f"Invalid configuration: {_e}", style="red")
            raise typer.Exit(1)

        if _project_uses_html_templates(project_config):
            _prepare_html_environment(
                setup_requested=setup_html,
                verbose=verbose,
                output_console=stderr_console,
            )

        stderr_console.print(
            f"Using YAML output directory: {project_config.project.output_dir}",
            style="blue",
        )

        generator = ScreenshotGenerator()

        stderr_console.print("Starting generation...", style="blue")

        try:
            config_dir = config_file.parent
            result_paths = generator.generate_project(project_config, config_dir)
            results = []
            for i, (screenshot_id, screenshot_def) in enumerate(
                project_config.screenshots.items()
            ):
                if i < len(result_paths):
                    results.append((screenshot_id, result_paths[i], True, None))
                else:
                    results.append((screenshot_id, None, False, "Generation failed"))
        except Exception as _e:
            stderr_console.print(f"Project generation failed: {_e}", style="red")
            raise typer.Exit(1)

        if json_mode:
            json_results = [
                {
                    "name": name,
                    "path": str(path) if path else None,
                    "success": success,
                    "error": error,
                }
                for name, path, success, error in results
            ]
            print(json.dumps(json_results))
        else:
            _show_results(results, project_config.project.output_dir)

        failed_count = sum(1 for _, _, success, _ in results if not success)
        if failed_count > 0:
            stderr_console.print(
                f"\n{failed_count} screenshot(s) failed to generate",
                style="yellow",
            )
            raise typer.Exit(1)

        if not json_mode:
            console.print(
                f"\nGenerated {len(results)} screenshots successfully!",
                style="green",
            )

    except KoubouError as e:
        stderr_console.print(f"{e}", style="red")
        raise typer.Exit(1)
    except Exception as _e:
        stderr_console.print(f"Unexpected error: {_e}", style="red")
        if verbose:
            stderr_console.print_exception()
        raise typer.Exit(1)


@app.command()
def setup_html(
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
):
    """Prepare HTML rendering support for the current Koubou installation."""

    setup_logging(verbose)

    try:
        status = setup_html_environment(verbose=verbose)
        if status.did_install_browser:
            console.print(
                "HTML ready: installed "
                f"{status.browser_name} for this Koubou environment",
                style="green",
            )
        else:
            console.print(f"HTML ready: using {status.browser_name}", style="green")
    except KoubouError as e:
        console.print(f"{e}", style="red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"{e}", style="red")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def list_sizes(
    output: str = typer.Option(
        "table", "--output", help="Output format: table or json"
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
) -> None:
    """List available App Store screenshot sizes"""
    from .config import load_appstore_sizes

    try:
        sizes = load_appstore_sizes()

        if output == "json":
            print(json.dumps(sizes))
            return

        table = Table(
            title="App Store Screenshot Sizes",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Size Name", style="green")
        table.add_column("Dimensions", style="yellow")
        table.add_column("Description", style="white")

        for size_name, size_info in sizes.items():
            width = int(size_info["width"])
            height = int(size_info["height"])
            description = str(size_info["description"])
            table.add_row(size_name, f"{width} x {height}", description)

        console.print(table)
        console.print(
            f"\nFound {len(sizes)} available App Store sizes",
            style="bold green",
        )
        console.print(
            '\nUsage: Set output_size: "iPhone6_9" in your YAML config',
            style="blue",
        )

    except Exception as e:
        console.print(f"Error listing sizes: {e}", style="red")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def list_frames(
    search: Optional[str] = typer.Argument(None, help="Filter frames by search term"),
    output: str = typer.Option(
        "table", "--output", help="Output format: table or json"
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
):
    """List all available device frame names with optional fuzzy search"""
    json_mode = output == "json"
    setup_logging(verbose, log_console=Console(stderr=True) if json_mode else None)

    try:
        generator = ScreenshotGenerator()
        all_frames = generator.device_frame_renderer.get_available_frames()

        if not all_frames:
            console.print("No device frames found", style="red")
            raise typer.Exit(1)

        if search:
            frames_to_display = [
                frame for frame in all_frames if search.lower() in frame.lower()
            ]
            if not frames_to_display:
                console.print(f"No frames found matching '{search}'", style="red")
                return
        else:
            frames_to_display = all_frames

        if output == "json":
            print(json.dumps(frames_to_display))
            return

        if search:
            console.print(
                f"Found {len(frames_to_display)} frames matching '{search}'",
                style="green",
            )
        else:
            console.print(
                f"Found {len(all_frames)} available device frames", style="green"
            )

        table = Table(
            title="Available Device Frames",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Frame Name", style="cyan", no_wrap=False)

        for frame_name in frames_to_display:
            table.add_row(frame_name)

        console.print(table)

        if not search:
            console.print(
                "\nTip: Use 'kou list-frames iPhone' to filter by device type",
                style="blue",
            )

    except Exception as e:
        console.print(f"Error listing frames: {e}", style="red")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def inspect_frame(
    device: str = typer.Argument(..., help="Exact device frame name to inspect"),
    output_size: str = typer.Option(
        "iPhone6_9",
        "--output-size",
        help="Named App Store size or custom dimensions like 1320x2868",
    ),
    output: str = typer.Option(
        "table", "--output", help="Output format: table or json"
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
):
    """Inspect frame geometry for layout and screenshot design decisions."""
    json_mode = output == "json"
    output_console = Console(stderr=True) if json_mode else console
    setup_logging(verbose, log_console=output_console if json_mode else None)

    try:
        resolved_output_size = _parse_output_size_option(output_size)
        generator = ScreenshotGenerator()
        inspection = generator.device_frame_renderer.inspect_frame(device)
        payload = _frame_inspection_payload(
            device=device,
            output_size=resolved_output_size,
            inspection=inspection,
        )

        if json_mode:
            print(json.dumps(payload))
            return

        summary = Table(
            title="Frame Inspection",
            show_header=True,
            header_style="bold cyan",
        )
        summary.add_column("Field", style="green")
        summary.add_column("Value", style="white")

        summary.add_row("Device", payload["device"])
        summary.add_row(
            "Output Size",
            f'{payload["output_size"]["width"]} x {payload["output_size"]["height"]}',
        )
        summary.add_row("Canvas Class", payload["canvas_class"])
        summary.add_row("Orientation", payload["orientation"])
        summary.add_row(
            "Frame Size",
            f'{payload["frame_size"]["width"]} x {payload["frame_size"]["height"]}',
        )
        summary.add_row(
            "Screen Bounds",
            (
                f'x={payload["screen_bounds"]["x"]}, '
                f'y={payload["screen_bounds"]["y"]}, '
                f'w={payload["screen_bounds"]["width"]}, '
                f'h={payload["screen_bounds"]["height"]}'
            ),
        )
        summary.add_row(
            "Screen BBox",
            (
                f'l={payload["screen_bbox"]["left"]}, '
                f't={payload["screen_bbox"]["top"]}, '
                f'r={payload["screen_bbox"]["right"]}, '
                f'b={payload["screen_bbox"]["bottom"]}'
            ),
        )
        summary.add_row(
            "Safe Margins",
            (
                f'l={payload["safe_margins"]["left"]}, '
                f't={payload["safe_margins"]["top"]}, '
                f'r={payload["safe_margins"]["right"]}, '
                f'b={payload["safe_margins"]["bottom"]}'
            ),
        )
        summary.add_row("Frame Ratio", f'{payload["frame_ratio"]:.4f}')
        summary.add_row("Screen Ratio", f'{payload["screen_ratio"]:.4f}')
        summary.add_row(
            "Screen Coverage",
            f'{payload["screen_coverage_ratio"]:.4f}',
        )

        console.print(summary)
        console.print(
            Panel(
                "Use this geometry to size typography, crop the device, and avoid "
                "under-scaled layouts on the real canvas.",
                title="Layout Tip",
                border_style="blue",
            )
        )

    except typer.BadParameter as e:
        output_console.print(str(e), style="red")
        raise typer.Exit(2)
    except Exception as e:
        output_console.print(f"Error inspecting frame: {e}", style="red")
        if verbose:
            output_console.print_exception()
        raise typer.Exit(1)


@app.command()
def live(
    config_file: Path = typer.Argument(..., help="YAML configuration file to watch"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
    debounce: float = typer.Option(0.5, "--debounce", help="Debounce delay in seconds"),
    setup_html: bool = typer.Option(
        False,
        "--setup-html",
        help="Prepare HTML rendering before starting live mode",
    ),
):
    """Live editing mode - regenerate screenshots when config or assets change"""

    setup_logging(verbose)

    try:
        if not config_file.exists():
            console.print(f"Configuration file not found: {config_file}", style="red")
            raise typer.Exit(1)

        try:
            with open(config_file) as f:
                config_data = yaml.safe_load(f)
            project_config = ProjectConfig(**config_data)
        except Exception:
            project_config = None

        if project_config and _project_uses_html_templates(project_config):
            _prepare_html_environment(
                setup_requested=setup_html,
                verbose=verbose,
                output_console=console,
            )

        live_generator = LiveScreenshotGenerator(config_file)
        watcher = LiveWatcher(config_file, debounce_delay=debounce)
        preview_server = None

        stop_event = False

        def signal_handler(signum, frame):
            nonlocal stop_event
            stop_event = True
            console.print("\nShutting down live mode...", style="yellow")

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        status_display = _create_live_status_display()

        with Live(status_display, console=console, refresh_per_second=4):
            console.print("Starting initial generation...", style="blue")
            initial_result = live_generator.initial_generation()

            if initial_result.has_errors:
                console.print("Initial generation had errors:", style="red")
                for error in initial_result.config_errors:
                    console.print(f"  - {error}", style="red")
                for screenshot_id, error in initial_result.failed_screenshots.items():
                    console.print(f"  - {screenshot_id}: {error}", style="red")
            else:
                console.print(
                    f"Initial generation complete: "
                    f"{initial_result.success_count} screenshots",
                    style="green",
                )

            if live_generator.has_preview_screenshots():
                preview_errors = live_generator.sync_preview_workspace()
                preview_server = HtmlPreviewServer(live_generator.preview_workspace)
                preview_server.set_slides(live_generator.get_preview_slides())
                preview_server.start()
                if preview_server.open_browser():
                    console.print(
                        f"Live preview: {preview_server.url}",
                        style="blue",
                    )
                else:
                    console.print(
                        f"Live preview: {preview_server.url}",
                        style="yellow",
                    )
                for screenshot_id, error in preview_errors.items():
                    console.print(
                        f"Preview build failed for {screenshot_id}: {error}",
                        style="red",
                    )
                    preview_server.publish_slide_error(screenshot_id, error)

            def on_files_changed(changed_files: Set[Path]):
                nonlocal preview_server
                console.print(
                    f"{len(changed_files)} file(s) changed, processing...",
                    style="cyan",
                )
                result = live_generator.handle_file_changes(changed_files)

                if result.regenerated_screenshots:
                    console.print(
                        f"Regenerated "
                        f"{len(result.regenerated_screenshots)} screenshot(s): "
                        f"{', '.join(result.regenerated_screenshots)}",
                        style="green",
                    )

                if result.failed_screenshots:
                    console.print("Some regenerations failed:", style="red")
                    for screenshot_id, error in result.failed_screenshots.items():
                        console.print(f"  - {screenshot_id}: {error}", style="red")

                if result.config_errors:
                    console.print("Config errors:", style="red")
                    for error in result.config_errors:
                        console.print(f"  - {error}", style="red")

                if live_generator.has_preview_screenshots():
                    if preview_server is None:
                        preview_errors = live_generator.sync_preview_workspace()
                        preview_server = HtmlPreviewServer(
                            live_generator.preview_workspace
                        )
                        preview_server.set_slides(live_generator.get_preview_slides())
                        preview_server.start()
                        if preview_server.open_browser():
                            console.print(
                                f"Live preview: {preview_server.url}",
                                style="blue",
                            )
                        else:
                            console.print(
                                f"Live preview: {preview_server.url}",
                                style="yellow",
                            )
                    elif result.preview_full_reload:
                        preview_errors = live_generator.sync_preview_workspace()
                        preview_server.set_slides(live_generator.get_preview_slides())
                        preview_server.publish_full_reload()
                    else:
                        updated_preview = set(result.updated_preview_screenshots)
                        preview_errors = (
                            live_generator.sync_preview_workspace(updated_preview)
                            if updated_preview
                            else {}
                        )
                        if updated_preview:
                            preview_server.publish_reload_slides(
                                sorted(updated_preview)
                            )

                    for screenshot_id, error in {
                        **result.preview_errors,
                        **preview_errors,
                    }.items():
                        console.print(
                            f"Preview update failed for {screenshot_id}: {error}",
                            style="red",
                        )
                        preview_server.publish_slide_error(screenshot_id, error)
                elif preview_server is not None:
                    live_generator.preview_workspace.remove_stale_slides([])
                    preview_server.set_slides([])
                    preview_server.publish_full_reload()

            watcher.set_change_callback(on_files_changed)

            asset_paths = live_generator.get_asset_paths()
            if asset_paths:
                watcher.add_asset_paths(asset_paths)
                console.print(
                    f"Watching {len(asset_paths)} asset file(s)", style="blue"
                )

            watcher.start()

            _update_live_status(
                status_display,
                live_generator,
                watcher,
                initial_result.success_count,
                initial_result.error_count,
            )

            console.print("Live mode active - press Ctrl+C to stop", style="green")
            console.print(f"Config: {config_file}", style="blue")
            console.print(f"Debounce: {debounce}s", style="blue")

            try:
                while not stop_event:
                    import time

                    time.sleep(0.1)
            except KeyboardInterrupt:
                pass

        watcher.stop()
        if preview_server:
            preview_server.stop()
        live_generator.close()
        console.print("Live mode stopped", style="green")

    except KoubouError as e:
        console.print(f"{e}", style="red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"Unexpected error: {e}", style="red")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


def _create_live_status_display():
    return Panel(
        Text("Starting live mode...", style="cyan"),
        title="Live Mode Status",
        border_style="blue",
    )


def _update_live_status(
    status_display, live_generator, watcher, success_count, error_count
):
    status_text = Text()
    status_text.append(f"Screenshots generated: {success_count}\n", style="green")
    if error_count > 0:
        status_text.append(f"Errors: {error_count}\n", style="red")

    watched_files = watcher.get_watched_files()
    status_text.append(f"Watching {len(watched_files)} file(s)\n", style="blue")

    dependency_info = live_generator.get_dependency_summary()
    status_text.append(
        f"Dependencies: {dependency_info['total_dependencies']}\n", style="cyan"
    )

    status_display.renderable = status_text


def main() -> None:
    app()


if __name__ == "__main__":
    main()

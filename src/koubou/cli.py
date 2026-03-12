"""Command line interface for Koubou."""

import json
import logging
import signal
from pathlib import Path
from typing import Optional, Set

import typer
import yaml
from rich.console import Console
from rich.live import Live
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .config import ProjectConfig
from .exceptions import KoubouError
from .generator import ScreenshotGenerator
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
    if output_file.exists() and not force:
        console.print(
            f"File {output_file} already exists. Use --force to overwrite.",
            style="red",
        )
        raise typer.Exit(1)

    sample_config = {
        "project": {
            "name": name,
            "output_dir": "Screenshots/Generated",
            "device": "iPhone 15 Pro Portrait",
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

    with open(output_file, "w") as f:
        yaml.dump(sample_config, f, default_flow_style=False, indent=2)

    console.print(f"Created sample configuration: {output_file}", style="green")
    console.print("\nEdit the configuration file and run:", style="blue")
    console.print(f"   kou generate {output_file}", style="cyan")


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
        _create_config_file(create_config, name, force=force)
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

            def on_files_changed(changed_files: Set[Path]):
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

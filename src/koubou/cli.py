"""Command line interface for Koubou."""

import logging
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from .config import ProjectConfig, ScreenshotConfig
from .exceptions import KoubouError
from .generator import ScreenshotGenerator

app = typer.Typer(
    name="kou",
    help="🎯 Koubou (工房) - The artisan workshop for App Store screenshots",
    add_completion=False,
)
console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Setup logging with rich formatting."""
    log_level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, show_path=False)],
    )


@app.command()
def generate(
    config_file: Path = typer.Argument(..., help="YAML configuration file"),
    output_dir: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output directory"
    ),
    frame_dir: Optional[str] = typer.Option(
        None, "--frames", "-", help="Device frames directory"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
) -> None:
    """Generate screenshots from configuration file."""

    setup_logging(verbose)

    try:
        # Load configuration
        if not config_file.exists():
            console.print(
                f"❌ Configuration file not found: {config_file}", style="red"
            )
            raise typer.Exit(1)

        with open(config_file) as f:
            config_data = yaml.safe_load(f)

        # Parse configuration
        try:
            project_config = ProjectConfig(**config_data)
            console.print("🎨 Using flexible content-based API", style="blue")
        except Exception as _e:
            console.print("❌ Invalid configuration: {e}", style="red")
            raise typer.Exit(1)

        # Override output directory only if explicitly provided AND not set in YAML
        if output_dir:
            project_config.project.output_dir = output_dir
            console.print(
                "📁 Overriding output directory: {output_dir}", style="yellow"
            )
        else:
            console.print(
                "📁 Using YAML output directory: {project_config.project.output_dir}",
                style="blue",
            )

        # Frame directory is passed to generator instead

        # Initialize generator
        generator = ScreenshotGenerator(frame_directory=frame_dir)

        # Generate screenshots with progress
        console.print("🚀 Starting generation...", style="blue")

        try:
            # Pass the config file directory for relative path resolution
            config_dir = config_file.parent
            result_paths = generator.generate_project(project_config, config_dir)
            # Convert to results format for display
            results = []
            for i, screenshot_def in enumerate(project_config.screenshots):
                if i < len(result_paths):
                    results.append((screenshot_def.name, result_paths[i], True, None))
                else:
                    results.append(
                        (screenshot_def.name, None, False, "Generation failed")
                    )
        except Exception as _e:
            console.print("❌ Project generation failed: {e}", style="red")
            raise typer.Exit(1)

        # Show results
        _show_results(results, project_config.project.output_dir)

        # Exit with error code if any failures
        failed_count = sum(1 for _, _, success, _ in results if not success)
        if failed_count > 0:
            console.print(
                "\n⚠️  {failed_count} screenshot(s) failed to generate", style="yellow"
            )
            raise typer.Exit(1)

        console.print(
            "\n✅ Generated {len(results)} screenshots successfully!", style="green"
        )

    except KoubouError as e:
        console.print("❌ {e}", style="red")
        raise typer.Exit(1)
    except Exception as _e:
        console.print("❌ Unexpected error: {e}", style="red")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def list_frames(
    frame_dir: Optional[str] = typer.Option(
        None, "--frames", "-", help="Device frames directory"
    ),
) -> None:
    """List available device frames."""

    generator = ScreenshotGenerator(frame_directory=frame_dir)
    frames = generator.device_frame_renderer.get_available_frames()

    if not frames:
        console.print("No device frames found.", style="yellow")
        return

    # Create table
    table = Table(
        title="Available Device Frames", show_header=True, header_style="bold magenta"
    )
    table.add_column("Frame Name", style="cyan")
    table.add_column("Size", style="green")

    for frame_name in frames:
        size = generator.device_frame_renderer.get_frame_size(frame_name)
        size_str = "{size[0]}×{size[1]}" if size else "Unknown"
        table.add_row(frame_name, size_str)

    console.print(table)


@app.command()
def create_config(
    output_file: Path = typer.Argument(..., help="Output configuration file path"),
    name: str = typer.Option(
        "My Screenshot Project", "--name", "-n", help="Project name"
    ),
) -> None:
    """Create a sample configuration file."""

    if output_file.exists():
        if not typer.confirm("File {output_file} already exists. Overwrite?"):
            raise typer.Exit(0)

    # Create sample configuration
    sample_config = {
        "project_name": name,
        "output_directory": "output",
        "screenshots": [
            {
                "name": "App Launch",
                "source_image": "screenshots/home.png",
                "device_frame": "iPhone 15 Pro - Natural Titanium - Portrait",
                "output_size": [1290, 2796],
                "background": {
                    "type": "linear",
                    "colors": ["#667eea", "#764ba2"],
                    "direction": 45,
                },
                "text_overlays": [
                    {
                        "content": "Beautiful App",
                        "position": [100, 200],
                        "font_size": 48,
                        "color": "#ffffff",
                        "alignment": "center",
                        "max_width": 600,
                    }
                ],
            }
        ],
    }

    with open(output_file, "w") as f:
        yaml.dump(sample_config, f, default_flow_style=False, indent=2)

    console.print("✅ Created sample configuration: {output_file}", style="green")
    console.print("\n📝 Edit the configuration file and run:", style="blue")
    console.print("   kou generate {output_file}", style="cyan")


def _show_results(results, output_dir: str) -> None:
    """Show generation results in a table."""

    table = Table(
        title="Generation Results", show_header=True, header_style="bold magenta"
    )
    table.add_column("Screenshot", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Output Path", style="blue")

    for name, path, success, error in results:
        if success:
            status = "✅ Success"
            output_path = str(path) if path else ""
        else:
            status = "❌ Failed"
            output_path = (
                error[:50] + "..." if error and len(error) > 50 else (error or "")
            )

        table.add_row(name, status, output_path)

    console.print(table)

    # Show output directory
    console.print("\n📁 Output directory: {Path(output_dir).absolute()}", style="blue")


@app.command()
def version() -> None:
    """Show version information."""

    console.print("🎯 Koubou v{__version__}", style="green")


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()

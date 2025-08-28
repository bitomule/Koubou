"""Command line interface for Koubou."""

import logging
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from .config import ProjectConfig
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


@app.command("create-config")
def create_config(
    output_file: Path = typer.Argument(..., help="Output configuration file path"),
    name: str = typer.Option(
        "My Screenshot Project", "--name", "-n", help="Project name"
    ),
) -> None:
    """Create a sample configuration file."""

    if output_file.exists():
        if not typer.confirm(f"File {output_file} already exists. Overwrite?"):
            raise typer.Exit(0)

    # Create sample configuration using real ProjectConfig format
    sample_config = {
        "project": {"name": name, "output_dir": "Screenshots/Generated"},
        "devices": ["iPhone 15 Pro Portrait"],
        "defaults": {
            "background": {
                "type": "linear",
                "colors": ["#E8F0FE", "#F8FBFF"],
                "direction": 180,
            }
        },
        "screenshots": [
            {
                "name": "welcome_screen",
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
            {
                "name": "features_screen",
                "content": [
                    {
                        "type": "text",
                        "content": "✨ Amazing Features",
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
            {
                "name": "gradient_showcase",
                "content": [
                    {
                        "type": "text",
                        "content": "🌈 Gradient Magic",
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
        ],
    }

    with open(output_file, "w") as f:
        yaml.dump(sample_config, f, default_flow_style=False, indent=2)

    console.print(f"✅ Created sample configuration: {output_file}", style="green")
    console.print("\n📝 Edit the configuration file and run:", style="blue")
    console.print(f"   kou {output_file}", style="cyan")


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
    console.print(f"\n📁 Output directory: {Path(output_dir).absolute()}", style="blue")


# Add global version option and primary config file handling
@app.callback()
def main_callback(
    config_file: Optional[Path] = typer.Argument(None, help="YAML configuration file"),
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit",
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
):
    """🎯 Koubou (工房) - The artisan workshop for App Store screenshots"""

    # Handle version flag
    if version:
        from koubou import __version__

        console.print(f"🎯 Koubou v{__version__}", style="green")
        raise typer.Exit()

    # If no config file provided, just show help
    if config_file is None:
        return

    # Generate screenshots from config file
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
            console.print(f"❌ Invalid configuration: {_e}", style="red")
            raise typer.Exit(1)

        console.print(
            f"📁 Using YAML output directory: {project_config.project.output_dir}",
            style="blue",
        )

        # Initialize generator (use internal frames)
        generator = ScreenshotGenerator()

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
            console.print(f"❌ Project generation failed: {_e}", style="red")
            raise typer.Exit(1)

        # Show results
        _show_results(results, project_config.project.output_dir)

        # Exit with error code if any failures
        failed_count = sum(1 for _, _, success, _ in results if not success)
        if failed_count > 0:
            console.print(
                f"\n⚠️  {failed_count} screenshot(s) failed to generate",
                style="yellow",
            )
            raise typer.Exit(1)

        console.print(
            f"\n✅ Generated {len(results)} screenshots successfully!",
            style="green",
        )

    except KoubouError as e:
        console.print(f"❌ {e}", style="red")
        raise typer.Exit(1)
    except Exception as _e:
        console.print(f"❌ Unexpected error: {_e}", style="red")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()

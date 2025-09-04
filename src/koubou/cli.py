"""Command line interface for Koubou."""

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

from .appstore.auth import (
    AppStoreAuth,
    AppStoreAuthError,
    AppStoreCredentials,
    create_config_file,
)
from .appstore.uploader import ScreenshotUploader, ScreenshotUploadError
from .config import ProjectConfig
from .exceptions import KoubouError
from .generator import ScreenshotGenerator
from .live_generator import LiveScreenshotGenerator
from .watcher import LiveWatcher

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


def _create_config_file(output_file: Path, name: str) -> None:
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
            "gradient_showcase": {
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
        },
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


# Main callback for global options
@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    create_config: Optional[Path] = typer.Option(
        None, "--create-config", help="Create a sample configuration file"
    ),
    name: str = typer.Option(
        "My Screenshot Project", "--name", "-n", help="Project name for config creation"
    ),
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit",
    ),
):
    """🎯 Koubou (工房) - The artisan workshop for App Store screenshots"""

    # Handle version flag
    if version:
        from koubou import __version__

        console.print(f"🎯 Koubou v{__version__}", style="green")
        raise typer.Exit()

    # Handle create-config functionality
    if create_config:
        _create_config_file(create_config, name)
        raise typer.Exit()

    # If no subcommand invoked, show help
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()


# Generate command (default when config file is provided)
@app.command()
def generate(
    config_file: Path = typer.Argument(..., help="YAML configuration file"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
):
    """Generate screenshots from YAML configuration file"""

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
            for i, (screenshot_id, screenshot_def) in enumerate(
                project_config.screenshots.items()
            ):
                if i < len(result_paths):
                    results.append((screenshot_id, result_paths[i], True, None))
                else:
                    results.append((screenshot_id, None, False, "Generation failed"))
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


@app.command()
def list_frames(
    search: Optional[str] = typer.Argument(None, help="Filter frames by search term"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
):
    """📱 List all available device frame names with optional fuzzy search"""
    setup_logging(verbose)

    try:
        # Initialize generator to access device frame renderer
        generator = ScreenshotGenerator()

        # Get all available frames
        all_frames = generator.device_frame_renderer.get_available_frames()

        if not all_frames:
            console.print("❌ No device frames found", style="red")
            raise typer.Exit(1)

        # Apply search filter if provided
        if search:
            filtered_frames = [
                frame for frame in all_frames if search.lower() in frame.lower()
            ]
            frames_to_display = filtered_frames

            if not filtered_frames:
                console.print(f"❌ No frames found matching '{search}'", style="red")
                return  # Exit normally without showing table

            console.print(
                f"📱 Found {len(filtered_frames)} frames matching '{search}'",
                style="green",
            )
        else:
            frames_to_display = all_frames
            console.print(
                f"📱 Found {len(all_frames)} available device frames", style="green"
            )

        # Create and display results table
        table = Table(
            title="🎯 Available Device Frames",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Frame Name", style="cyan", no_wrap=False)

        # Add frames to table
        for frame_name in frames_to_display:
            table.add_row(frame_name)

        console.print(table)

        # Show usage tip
        if not search:
            console.print(
                "\n💡 Tip: Use 'kou list-frames iPhone' to filter by device type",
                style="blue",
            )

    except Exception as e:
        console.print(f"❌ Error listing frames: {e}", style="red")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def live(
    config_file: Path = typer.Argument(..., help="YAML configuration file to watch"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
    debounce: float = typer.Option(0.5, "--debounce", help="Debounce delay in seconds"),
):
    """🔄 Live editing mode - regenerate screenshots when config or assets change"""

    setup_logging(verbose)

    try:
        # Validate config file exists
        if not config_file.exists():
            console.print(
                f"❌ Configuration file not found: {config_file}", style="red"
            )
            raise typer.Exit(1)

        # Initialize live generator and watcher
        live_generator = LiveScreenshotGenerator(config_file)
        watcher = LiveWatcher(config_file, debounce_delay=debounce)

        # Setup signal handling for graceful shutdown
        stop_event = False

        def signal_handler(signum, frame):
            nonlocal stop_event
            stop_event = True
            console.print("\n🛑 Shutting down live mode...", style="yellow")

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Create status display
        status_display = _create_live_status_display()

        with Live(status_display, console=console, refresh_per_second=4):
            # Initial generation
            console.print("🚀 Starting initial generation...", style="blue")
            initial_result = live_generator.initial_generation()

            if initial_result.has_errors:
                console.print("❌ Initial generation had errors:", style="red")
                for error in initial_result.config_errors:
                    console.print(f"  • {error}", style="red")
                for screenshot_id, error in initial_result.failed_screenshots.items():
                    console.print(f"  • {screenshot_id}: {error}", style="red")
            else:
                console.print(
                    f"✅ Initial generation complete: "
                    f"{initial_result.success_count} screenshots",
                    style="green",
                )

            # Setup file change callback
            def on_files_changed(changed_files: Set[Path]):
                console.print(
                    f"📝 {len(changed_files)} file(s) changed, processing...",
                    style="cyan",
                )
                result = live_generator.handle_file_changes(changed_files)

                if result.regenerated_screenshots:
                    console.print(
                        f"✅ Regenerated "
                        f"{len(result.regenerated_screenshots)} screenshot(s): "
                        f"{', '.join(result.regenerated_screenshots)}",
                        style="green",
                    )

                if result.failed_screenshots:
                    console.print("❌ Some regenerations failed:", style="red")
                    for screenshot_id, error in result.failed_screenshots.items():
                        console.print(f"  • {screenshot_id}: {error}", style="red")

                if result.config_errors:
                    console.print("❌ Config errors:", style="red")
                    for error in result.config_errors:
                        console.print(f"  • {error}", style="red")

            # Start watching
            watcher.set_change_callback(on_files_changed)

            # Add asset paths to watcher
            asset_paths = live_generator.get_asset_paths()
            if asset_paths:
                watcher.add_asset_paths(asset_paths)
                console.print(
                    f"👁️  Watching {len(asset_paths)} asset file(s)", style="blue"
                )

            watcher.start()

            # Update status display
            _update_live_status(
                status_display,
                live_generator,
                watcher,
                initial_result.success_count,
                initial_result.error_count,
            )

            console.print("👁️  Live mode active - press Ctrl+C to stop", style="green")
            console.print(f"📁 Config: {config_file}", style="blue")
            console.print(f"⏱️  Debounce: {debounce}s", style="blue")

            # Keep running until signal received
            try:
                while not stop_event:
                    import time

                    time.sleep(0.1)
            except KeyboardInterrupt:
                pass

        # Cleanup
        watcher.stop()
        console.print("✅ Live mode stopped", style="green")

    except KoubouError as e:
        console.print(f"❌ {e}", style="red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


def _create_live_status_display():
    """Create the status display for live mode."""
    return Panel(
        Text("Starting live mode...", style="cyan"),
        title="🔄 Live Mode Status",
        border_style="blue",
    )


def _update_live_status(
    status_display, live_generator, watcher, success_count, error_count
):
    """Update the live status display with current information."""
    status_text = Text()
    status_text.append(f"✅ Screenshots generated: {success_count}\n", style="green")
    if error_count > 0:
        status_text.append(f"❌ Errors: {error_count}\n", style="red")

    watched_files = watcher.get_watched_files()
    status_text.append(f"👁️  Watching {len(watched_files)} file(s)\n", style="blue")

    dependency_info = live_generator.get_dependency_summary()
    status_text.append(
        f"📦 Dependencies: {dependency_info['total_dependencies']}\n", style="cyan"
    )

    status_display.renderable = status_text


@app.command()
def upload(
    config_file: Path = typer.Argument(..., help="YAML configuration file"),
    setup: bool = typer.Option(
        False, "--setup", help="Setup App Store Connect credentials only"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview upload without actually uploading"
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
):
    """📱 Upload generated screenshots to App Store Connect"""

    setup_logging(verbose)

    try:
        # Validate config file exists
        if not config_file.exists():
            console.print(
                f"❌ Configuration file not found: {config_file}", style="red"
            )
            raise typer.Exit(1)

        # Determine App Store config path (next to YAML config)
        appstore_config_path = config_file.parent / "appstore-config.json"

        # Handle setup-only mode
        if setup:
            _setup_appstore_credentials(appstore_config_path)
            raise typer.Exit(0)

        # Check for existing App Store config
        if not appstore_config_path.exists():
            console.print(
                f"❌ App Store Connect config not found: {appstore_config_path.name}",
                style="red",
            )

            # Ask user if they want to create it
            create_config = typer.confirm("? Would you like to create it now?")
            if create_config:
                _setup_appstore_credentials(appstore_config_path)
                console.print(
                    "\nℹ️ Setup complete! Run the upload command again to upload screenshots.",
                    style="blue",
                )
                raise typer.Exit(0)
            else:
                console.print("💡 You can create the config later with:", style="blue")
                console.print(f"   kou upload --setup {config_file}", style="cyan")
                raise typer.Exit(1)

        # Load App Store credentials
        try:
            credentials = AppStoreCredentials.from_config_file(appstore_config_path)
            console.print("✅ Loaded App Store Connect credentials", style="green")
        except AppStoreAuthError as e:
            console.print(f"❌ Invalid App Store Connect config: {e}", style="red")
            console.print("💡 Fix the config or recreate it with:", style="blue")
            console.print(f"   kou upload --setup {config_file}", style="cyan")
            raise typer.Exit(1)

        # Validate credentials by generating a test token
        try:
            auth = AppStoreAuth(credentials)
            auth.validate_credentials()
            console.print("✅ App Store Connect credentials validated", style="green")
        except AppStoreAuthError as e:
            console.print(f"❌ Credential validation failed: {e}", style="red")
            raise typer.Exit(1)

        # Find generated screenshots directory
        with open(config_file) as f:
            config_data = yaml.safe_load(f)

        project_config = ProjectConfig(**config_data)
        screenshots_dir = Path(config_file.parent) / project_config.project.output_dir

        if not screenshots_dir.exists():
            console.print(
                f"❌ Screenshots directory not found: {screenshots_dir}", style="red"
            )
            console.print("💡 Generate screenshots first with:", style="blue")
            console.print(f"   kou {config_file}", style="cyan")
            raise typer.Exit(1)

        # Initialize uploader and analyze screenshots
        uploader = ScreenshotUploader(credentials)

        try:
            console.print("🔍 Analyzing generated screenshots...", style="blue")
            screenshot_infos = uploader.analyze_screenshots(screenshots_dir)

            console.print(
                f"✅ Found {len(screenshot_infos)} valid screenshots", style="green"
            )

            # Show preview of what will be uploaded
            _show_upload_preview(screenshot_infos)

            if dry_run:
                console.print(
                    "\n🧪 Dry run complete - no screenshots were uploaded",
                    style="yellow",
                )
                raise typer.Exit(0)

            # Confirm upload
            if not typer.confirm("\n? Proceed with upload?"):
                console.print("Upload cancelled", style="yellow")
                raise typer.Exit(0)

            # Perform upload
            console.print("\n🚀 Starting upload to App Store Connect...", style="blue")
            results = uploader.upload_screenshots(screenshot_infos)

            # Show results
            _show_upload_results(results)

            # Exit with appropriate code
            failed_count = sum(1 for r in results if not r.success)
            if failed_count > 0:
                console.print(
                    f"\n⚠️ {failed_count} screenshot(s) failed to upload", style="yellow"
                )
                raise typer.Exit(1)

            console.print(
                f"\n✅ Successfully uploaded {len(results)} screenshots!", style="green"
            )

        except ScreenshotUploadError as e:
            console.print(f"❌ Upload failed: {e}", style="red")
            raise typer.Exit(1)

    except KoubouError as e:
        console.print(f"❌ {e}", style="red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


def _setup_appstore_credentials(config_path: Path) -> None:
    """Interactive setup of App Store Connect credentials."""
    console.print("📝 Setting up App Store Connect integration...", style="blue")

    # Collect credentials interactively
    key_id = typer.prompt("? Key ID (from App Store Connect)")
    issuer_id = typer.prompt("? Issuer ID (from App Store Connect)")
    private_key_path = typer.prompt(
        "? Private key file path", default="./AuthKey_" + key_id + ".p8"
    )
    app_id = typer.prompt("? App ID (from App Store Connect)")

    # Validate private key file exists
    key_path = Path(private_key_path).expanduser()
    if not key_path.is_absolute():
        key_path = config_path.parent / key_path

    if not key_path.exists():
        console.print(f"❌ Private key file not found: {key_path}", style="red")
        raise typer.Exit(1)

    # Create config
    credentials_data = {
        "key_id": key_id,
        "issuer_id": issuer_id,
        "private_key_path": private_key_path,
        "app_id": app_id,
    }

    try:
        create_config_file(config_path, credentials_data)
        console.print(f"✅ Created {config_path.name}", style="green")

        # Test credentials
        credentials = AppStoreCredentials.from_config_file(config_path)
        auth = AppStoreAuth(credentials)
        auth.validate_credentials()
        console.print("✅ Credentials validated successfully", style="green")

    except (AppStoreAuthError, Exception) as e:
        console.print(f"❌ Setup failed: {e}", style="red")
        # Clean up failed config file
        if config_path.exists():
            config_path.unlink()
        raise typer.Exit(1)


def _show_upload_preview(screenshot_infos) -> None:
    """Show preview of screenshots to be uploaded."""
    table = Table(
        title="📤 Upload Preview", show_header=True, header_style="bold magenta"
    )
    table.add_column("Screenshot", style="cyan")
    table.add_column("Device Type", style="green")
    table.add_column("App Store Type", style="blue")
    table.add_column("Size", style="yellow")

    for info in screenshot_infos:
        table.add_row(
            info.path.name,
            info.device_type,
            info.display_type,
            f"{info.size[0]}×{info.size[1]}",
        )

    console.print(table)


def _show_upload_results(results) -> None:
    """Show upload results in a table."""
    table = Table(
        title="📱 Upload Results", show_header=True, header_style="bold magenta"
    )
    table.add_column("Screenshot", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="blue")

    for result in results:
        if result.success:
            status = "✅ Success"
            details = result.screenshot_id or "Uploaded"
        else:
            status = "❌ Failed"
            details = result.error_message or "Unknown error"

        table.add_row(result.screenshot_path.name, status, details)

    console.print(table)


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()

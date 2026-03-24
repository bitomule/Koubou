"""On-demand device frame download and cache management."""

from __future__ import annotations

import logging
import pathlib
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TransferSpeedColumn,
)

from .exceptions import FramesNotAvailableError

logger = logging.getLogger(__name__)

FRAMES_CACHE_DIR = Path.home() / ".koubou" / "frames"
GITHUB_RELEASE_URL = (
    "https://github.com/bitomule/Koubou/releases/download/"
    "v{version}/frames-v{version}.tar.gz"
)


def _get_version() -> str:
    from . import __version__

    return __version__


def _contains_frame_pngs(path: Path) -> bool:
    return path.is_dir() and any(path.glob("*.png"))


def _find_checkout_frames_path(start: Optional[Path] = None) -> Optional[Path]:
    """Find frames in a source checkout when installed assets are absent."""
    current = (start or pathlib.Path.cwd()).resolve()
    for candidate_root in (current, *current.parents):
        frames = candidate_root / "src" / "koubou" / "frames"
        if _contains_frame_pngs(frames):
            return frames
    return None


def get_bundled_frames_path() -> Optional[Path]:
    """Return bundled frames, or source-checkout frames when running from a repo."""
    bundled = Path(__file__).parent / "frames"
    if _contains_frame_pngs(bundled):
        return bundled
    return _find_checkout_frames_path()


def get_cached_frames_path() -> Optional[Path]:
    """Return the cached frames path if it exists and has PNGs."""
    version = _get_version()
    cached = FRAMES_CACHE_DIR / version
    if _contains_frame_pngs(cached):
        return cached
    return None


def resolve_frames_path() -> Optional[Path]:
    """Return the best available frames path, or None if frames aren't available."""
    return get_bundled_frames_path() or get_cached_frames_path()


def download_frames(verbose: bool = False) -> Path:
    """Download frames tarball from GitHub Releases and extract to cache."""
    version = _get_version()
    if version == "dev" or ".dev" in version or "+" in version:
        raise FramesNotAvailableError(
            "Cannot download frames for development version. "
            "Use a source checkout, run from the repository root, or specify "
            "--frame-directory."
        )

    url = GITHUB_RELEASE_URL.format(version=version)
    dest = FRAMES_CACHE_DIR / version
    dest.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading device frames from {url}")

    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        _download_with_progress(url, tmp_path, verbose)
        _extract_tarball(tmp_path, dest)
    except Exception as exc:
        # Clean up partial download
        if dest.exists():
            import shutil

            shutil.rmtree(dest, ignore_errors=True)
        raise FramesNotAvailableError(
            f"Failed to download device frames: {exc}\n"
            "Check your internet connection and try again with: kou setup-frames"
        ) from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    if not any(dest.glob("*.png")):
        raise FramesNotAvailableError(
            "Downloaded archive did not contain any frame PNGs. "
            "This may indicate a corrupted release. "
            "Please report at https://github.com/bitomule/Koubou/issues"
        )

    return dest


def _download_with_progress(url: str, dest: Path, verbose: bool) -> None:
    """Download a URL to a file with a Rich progress bar."""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        total = int(response.headers.get("Content-Length", 0))

        with Progress(
            TextColumn("[bold blue]Downloading frames"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            disable=not verbose and total == 0,
        ) as progress:
            task = progress.add_task("download", total=total or None)
            with open(dest, "wb") as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))


def _extract_tarball(tarball: Path, dest: Path) -> None:
    """Extract a tar.gz into dest, flattening one level if needed."""
    with tarfile.open(tarball, "r:gz") as tar:
        # Check if all members are under a single directory
        members = tar.getmembers()
        top_dirs = {m.name.split("/")[0] for m in members if "/" in m.name}

        if len(top_dirs) == 1:
            # Flatten: strip the top-level directory prefix
            prefix = top_dirs.pop() + "/"
            for member in members:
                if member.name == prefix.rstrip("/"):
                    continue
                member.name = member.name[len(prefix) :]
                if member.name:
                    tar.extract(member, dest, filter="data")
        else:
            tar.extractall(dest, filter="data")


def ensure_frames(verbose: bool = False) -> Path:
    """Resolve frames path, auto-downloading if necessary."""
    path = resolve_frames_path()
    if path is not None:
        return path

    return download_frames(verbose=verbose)

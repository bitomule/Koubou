"""Shared HTML staging helpers for preview and final rendering."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Dict, Optional


def _remove_existing(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _symlink_or_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(source, destination)
    except OSError:
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)


def stage_html_workspace(
    *,
    template_path: Path,
    variables: Dict[str, str],
    destination_dir: Path,
    assets: Optional[Dict[str, str]] = None,
) -> Path:
    """Materialize a template into a stable workspace directory.

    The staged workspace mirrors the template directory layout, writes a processed
    ``index.html`` entrypoint, and mounts explicit assets so preview and final
    rendering can share the same prepared document root.
    """

    destination_dir.mkdir(parents=True, exist_ok=True)

    template_path = template_path.resolve()
    template_dir = template_path.parent

    for item in template_dir.iterdir():
        if item.resolve() == template_path:
            continue
        target = destination_dir / item.name
        if target.exists() or target.is_symlink():
            _remove_existing(target)
        _symlink_or_copy(item, target)

    if assets:
        for rel_name, abs_path in assets.items():
            source = Path(abs_path)
            target = destination_dir / rel_name
            if (
                target.exists() or target.is_symlink()
            ) and source.resolve() == target.resolve():
                continue
            if target.exists() or target.is_symlink():
                _remove_existing(target)
            _symlink_or_copy(source, target)

    html_content = template_path.read_text(encoding="utf-8")
    for key, value in variables.items():
        html_content = html_content.replace(f"{{{{{key}}}}}", value)

    index_path = destination_dir / "index.html"
    index_path.write_text(html_content, encoding="utf-8")
    return index_path

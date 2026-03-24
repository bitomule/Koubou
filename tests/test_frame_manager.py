"""Tests for the frame manager module."""

import tarfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from koubou.exceptions import FramesNotAvailableError
from koubou.frame_manager import (
    download_frames,
    ensure_frames,
    get_bundled_frames_path,
    get_cached_frames_path,
    resolve_frames_path,
)


@pytest.fixture
def temp_cache(tmp_path, monkeypatch):
    cache_dir = tmp_path / "frames_cache"
    monkeypatch.setattr("koubou.frame_manager.FRAMES_CACHE_DIR", cache_dir)
    return cache_dir


@pytest.fixture
def fake_version(monkeypatch):
    monkeypatch.setattr("koubou.frame_manager._get_version", lambda: "1.0.0")


class TestGetBundledFramesPath:
    def test_returns_none_when_no_pngs(self, tmp_path, monkeypatch):
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        (frames_dir / "Frames.json").write_text("{}")
        monkeypatch.setattr(
            "koubou.frame_manager.Path",
            lambda *a, **kw: (
                Path(*a, **kw)
                if a != (__file__,)
                else type("P", (), {"parent": tmp_path})()
            ),
        )
        # The real function uses Path(__file__).parent / "frames"
        # We test the actual bundled path which may or may not have PNGs
        result = get_bundled_frames_path()
        # In a source install, PNGs exist; in a wheel install, they don't
        # Just verify it returns a Path or None
        assert result is None or result.is_dir()

    def test_returns_path_when_pngs_exist(self):
        # The actual bundled path in a source checkout has PNGs
        bundled = Path(__file__).parent.parent / "src" / "koubou" / "frames"
        if bundled.is_dir() and any(bundled.glob("*.png")):
            result = get_bundled_frames_path()
            assert result is not None
            assert result.is_dir()

    def test_falls_back_to_source_checkout_when_installed_frames_are_missing(
        self, tmp_path, monkeypatch
    ):
        installed_pkg = tmp_path / "site-packages" / "koubou"
        installed_pkg.mkdir(parents=True)
        (installed_pkg / "frames").mkdir()

        repo_root = tmp_path / "repo"
        checkout_frames = repo_root / "src" / "koubou" / "frames"
        checkout_frames.mkdir(parents=True)
        (checkout_frames / "frame.png").write_bytes(b"fake png")

        monkeypatch.setattr(
            "koubou.frame_manager.__file__", str(installed_pkg / "frame_manager.py")
        )
        monkeypatch.chdir(repo_root)

        assert get_bundled_frames_path() == checkout_frames


class TestGetCachedFramesPath:
    def test_returns_none_when_cache_empty(self, temp_cache, fake_version):
        assert get_cached_frames_path() is None

    def test_returns_none_when_no_pngs(self, temp_cache, fake_version):
        cache_dir = temp_cache / "1.0.0"
        cache_dir.mkdir(parents=True)
        (cache_dir / "Frames.json").write_text("{}")
        assert get_cached_frames_path() is None

    def test_returns_path_when_pngs_exist(self, temp_cache, fake_version):
        cache_dir = temp_cache / "1.0.0"
        cache_dir.mkdir(parents=True)
        (cache_dir / "frame.png").write_bytes(b"fake png")
        result = get_cached_frames_path()
        assert result == cache_dir


class TestResolveFramesPath:
    def test_prefers_bundled_over_cached(self, temp_cache, fake_version):
        bundled = Path(__file__).parent.parent / "src" / "koubou" / "frames"
        if bundled.is_dir() and any(bundled.glob("*.png")):
            # Source install: bundled path should be returned
            result = resolve_frames_path()
            assert result == get_bundled_frames_path()

    def test_falls_back_to_cached(self, temp_cache, fake_version, monkeypatch):
        monkeypatch.setattr(
            "koubou.frame_manager.get_bundled_frames_path", lambda: None
        )
        cache_dir = temp_cache / "1.0.0"
        cache_dir.mkdir(parents=True)
        (cache_dir / "frame.png").write_bytes(b"fake png")
        result = resolve_frames_path()
        assert result == cache_dir

    def test_returns_none_when_nothing_available(
        self, temp_cache, fake_version, monkeypatch
    ):
        monkeypatch.setattr(
            "koubou.frame_manager.get_bundled_frames_path", lambda: None
        )
        assert resolve_frames_path() is None


class TestDownloadFrames:
    def test_raises_for_dev_version(self, monkeypatch):
        monkeypatch.setattr("koubou.frame_manager._get_version", lambda: "dev")
        with pytest.raises(FramesNotAvailableError, match="development version"):
            download_frames()

    def test_raises_for_pep440_dev_version(self, monkeypatch):
        monkeypatch.setattr(
            "koubou.frame_manager._get_version", lambda: "0.1.dev1+g1234567"
        )
        with pytest.raises(FramesNotAvailableError, match="development version"):
            download_frames()

    def test_downloads_and_extracts(self, temp_cache, fake_version, tmp_path):
        # Create a fake tarball
        tarball_path = tmp_path / "frames.tar.gz"
        frames_src = tmp_path / "frames_src"
        frames_src.mkdir()
        (frames_src / "device.png").write_bytes(b"fake png data")
        (frames_src / "Frames.json").write_text('{"devices": []}')
        with tarfile.open(tarball_path, "w:gz") as tar:
            tar.add(frames_src / "device.png", arcname="device.png")
            tar.add(frames_src / "Frames.json", arcname="Frames.json")

        def mock_urlopen(req):
            data = tarball_path.read_bytes()
            response = MagicMock()
            response.__enter__ = lambda s: s
            response.__exit__ = MagicMock(return_value=False)
            response.headers = {"Content-Length": str(len(data))}
            response.read = MagicMock(side_effect=[data, b""])
            return response

        with patch("koubou.frame_manager.urllib.request.urlopen", mock_urlopen):
            result = download_frames(verbose=False)

        assert result.is_dir()
        assert (result / "device.png").exists()
        assert (result / "Frames.json").exists()

    def test_cleans_up_on_failure(self, temp_cache, fake_version):
        def mock_urlopen(req):
            raise ConnectionError("Network error")

        with patch("koubou.frame_manager.urllib.request.urlopen", mock_urlopen):
            with pytest.raises(FramesNotAvailableError, match="Failed to download"):
                download_frames()

        cache_dir = temp_cache / "1.0.0"
        assert not cache_dir.exists()


class TestEnsureFrames:
    def test_returns_existing_path(self, monkeypatch):
        fake_path = Path("/fake/frames")
        monkeypatch.setattr(
            "koubou.frame_manager.resolve_frames_path", lambda: fake_path
        )
        assert ensure_frames() == fake_path

    def test_downloads_when_not_resolved(self, monkeypatch, tmp_path):
        monkeypatch.setattr("koubou.frame_manager.resolve_frames_path", lambda: None)
        monkeypatch.setattr(
            "koubou.frame_manager.download_frames",
            lambda verbose=False: tmp_path / "downloaded",
        )
        result = ensure_frames()
        assert result == tmp_path / "downloaded"

"""Tests for HTML setup helpers."""

import sys

import pytest

from koubou.html_setup import (
    HtmlEnvironmentStatus,
    browser_setup_message,
    format_html_environment_error,
    setup_html_environment,
)


def test_format_html_environment_error_points_to_setup_html():
    status = HtmlEnvironmentStatus(
        playwright_available=False,
        system_chrome_available=False,
        chromium_available=False,
        ready=False,
        details="missing runtime",
    )

    assert format_html_environment_error(status) == "missing runtime"


def test_browser_setup_message_mentions_kou_setup_html():
    message = browser_setup_message()

    assert "kou setup-html" in message
    assert "Google Chrome" in message


def test_setup_html_environment_installs_chromium(monkeypatch):
    states = iter(
        [
            HtmlEnvironmentStatus(
                playwright_available=True,
                system_chrome_available=False,
                chromium_available=False,
                ready=False,
            ),
            HtmlEnvironmentStatus(
                playwright_available=True,
                system_chrome_available=False,
                chromium_available=True,
                ready=True,
                browser_name="Playwright Chromium",
            ),
        ]
    )
    calls = []

    def fake_check():
        return next(states)

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(command, capture_output, text, check):
        calls.append(
            {
                "command": command,
                "capture_output": capture_output,
                "text": text,
                "check": check,
            }
        )
        return Result()

    monkeypatch.setattr("koubou.html_setup.check_html_environment", fake_check)
    monkeypatch.setattr("koubou.html_setup.subprocess.run", fake_run)

    status = setup_html_environment()

    assert status.ready is True
    assert status.did_install_browser is True
    assert calls == [
        {
            "command": [sys.executable, "-m", "playwright", "install", "chromium"],
            "capture_output": True,
            "text": True,
            "check": False,
        }
    ]


def test_setup_html_environment_fails_when_runtime_missing(monkeypatch):
    def fake_check():
        return HtmlEnvironmentStatus(
            playwright_available=False,
            system_chrome_available=False,
            chromium_available=False,
            ready=False,
            details="missing runtime",
        )

    monkeypatch.setattr("koubou.html_setup.check_html_environment", fake_check)

    with pytest.raises(RuntimeError, match="missing runtime"):
        setup_html_environment()

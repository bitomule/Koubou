"""Helpers for HTML rendering environment checks and setup."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from typing import Optional

HTML_SETUP_COMMAND = "kou setup-html"


@dataclass
class HtmlEnvironmentStatus:
    """Structured HTML environment readiness status."""

    playwright_available: bool
    system_chrome_available: bool
    chromium_available: bool
    ready: bool
    browser_name: Optional[str] = None
    details: Optional[str] = None
    did_install_browser: bool = False


def missing_playwright_message() -> str:
    """Explain how to recover when Playwright is missing from the install."""

    return (
        "HTML rendering support is missing from this Koubou installation. "
        f"Update Koubou to v0.15.1 or later, then run `{HTML_SETUP_COMMAND}`."
    )


def browser_setup_message(details: Optional[str] = None) -> str:
    """Explain how to recover when no browser is available."""

    message = (
        "HTML rendering is not set up yet. "
        f"Run `{HTML_SETUP_COMMAND}` to install Playwright Chromium, "
        "or install Google Chrome."
    )
    if details:
        return f"{message}\nDetails: {details}"
    return message


def import_sync_playwright():
    """Import Playwright lazily so non-HTML workflows stay lightweight."""

    try:
        from playwright.sync_api import sync_playwright

        return sync_playwright
    except ImportError as exc:
        raise RuntimeError(missing_playwright_message()) from exc


def check_html_environment() -> HtmlEnvironmentStatus:
    """Detect whether HTML rendering can run in the current environment."""

    try:
        sync_playwright = import_sync_playwright()
    except RuntimeError as exc:
        return HtmlEnvironmentStatus(
            playwright_available=False,
            system_chrome_available=False,
            chromium_available=False,
            ready=False,
            details=str(exc),
        )

    playwright = sync_playwright().start()
    chrome_error: Optional[Exception] = None
    chromium_error: Optional[Exception] = None

    try:
        try:
            browser = playwright.chromium.launch(channel="chrome")
            browser.close()
            return HtmlEnvironmentStatus(
                playwright_available=True,
                system_chrome_available=True,
                chromium_available=False,
                ready=True,
                browser_name="system Chrome",
            )
        except Exception as exc:
            chrome_error = exc

        try:
            browser = playwright.chromium.launch()
            browser.close()
            return HtmlEnvironmentStatus(
                playwright_available=True,
                system_chrome_available=False,
                chromium_available=True,
                ready=True,
                browser_name="Playwright Chromium",
            )
        except Exception as exc:
            chromium_error = exc

        detail_parts = []
        if chrome_error:
            detail_parts.append(f"Chrome: {chrome_error}")
        if chromium_error:
            detail_parts.append(f"Chromium: {chromium_error}")

        return HtmlEnvironmentStatus(
            playwright_available=True,
            system_chrome_available=False,
            chromium_available=False,
            ready=False,
            details=" | ".join(detail_parts) if detail_parts else None,
        )
    finally:
        playwright.stop()


def format_html_environment_error(status: HtmlEnvironmentStatus) -> str:
    """Convert readiness status into a user-facing actionable error."""

    if not status.playwright_available:
        return status.details or missing_playwright_message()
    return browser_setup_message(status.details)


def setup_html_environment(verbose: bool = False) -> HtmlEnvironmentStatus:
    """Ensure the current environment is ready for HTML rendering."""

    status = check_html_environment()
    if status.ready:
        return status

    if not status.playwright_available:
        raise RuntimeError(format_html_environment_error(status))

    command = [sys.executable, "-m", "playwright", "install", "chromium"]
    result = subprocess.run(
        command,
        capture_output=not verbose,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        details = None
        if not verbose:
            details = (result.stderr or result.stdout).strip() or None
        raise RuntimeError(
            browser_setup_message(details or "Failed to install Playwright Chromium.")
        )

    final_status = check_html_environment()
    final_status.did_install_browser = True
    if not final_status.ready:
        raise RuntimeError(format_html_environment_error(final_status))
    return final_status

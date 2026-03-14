"""Pytest fixtures for Nexus E2E tests with Playwright."""

import os
import subprocess
import signal
import time
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright, Browser, Page

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
SCREENSHOTS_DIR = Path(__file__).resolve().parent / "screenshots"
BASE_URL = "http://localhost:3000"
API_URL = "http://localhost:8001"


@pytest.fixture(scope="session")
def ensure_screenshots_dir():
    """Create screenshots directory if it doesn't exist."""
    SCREENSHOTS_DIR.mkdir(exist_ok=True)
    return SCREENSHOTS_DIR


@pytest.fixture(scope="session")
def browser_instance():
    """Launch a single browser instance for the entire test session."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless="--headed" not in " ".join(os.sys.argv),
        )
        yield browser
        browser.close()


@pytest.fixture
def page(browser_instance: Browser, ensure_screenshots_dir):
    """Create a fresh page (tab) for each test."""
    context = browser_instance.new_context(
        viewport={"width": 1280, "height": 800},
        locale="zh-TW",
    )
    pg = context.new_page()
    yield pg
    context.close()


@pytest.fixture
def mobile_page(browser_instance: Browser, ensure_screenshots_dir):
    """Create a mobile-sized page for responsive tests."""
    context = browser_instance.new_context(
        viewport={"width": 390, "height": 844},
        locale="zh-TW",
        is_mobile=True,
    )
    pg = context.new_page()
    yield pg
    context.close()


@pytest.fixture
def tablet_page(browser_instance: Browser, ensure_screenshots_dir):
    """Create a tablet-sized page for responsive tests."""
    context = browser_instance.new_context(
        viewport={"width": 768, "height": 1024},
        locale="zh-TW",
    )
    pg = context.new_page()
    yield pg
    context.close()


def screenshot(page: Page, name: str):
    """Helper to save a screenshot with a descriptive name."""
    path = SCREENSHOTS_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    return path

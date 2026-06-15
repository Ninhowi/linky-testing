"""Inject the E2E secret into browser localStorage before app navigation."""

from __future__ import annotations

import os

from selenium.webdriver.remote.webdriver import WebDriver

E2E_INJECT_STORAGE_KEY = "linky-e2e-key"


def inject_e2e_key(driver: WebDriver, base_url: str) -> None:
    key = os.environ.get("E2E_SECRET_KEY", "").strip()
    if not key:
        return
    normalized = base_url.rstrip("/")
    driver.get(normalized)
    driver.execute_script(
        "window.localStorage.setItem(arguments[0], arguments[1]);",
        E2E_INJECT_STORAGE_KEY,
        key,
    )

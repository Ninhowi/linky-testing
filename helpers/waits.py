"""Selenium wait helpers for Clerk auth flows.

Hàm chờ Selenium cho luồng xác thực Clerk.
"""

from __future__ import annotations

from collections.abc import Callable

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

DEFAULT_TIMEOUT_SEC = 10.0

_CLERK_READY = ("css selector", '[data-clerk-ready="true"]')


def wait_visible(
    driver: WebDriver,
    locator: tuple[str, str],
    timeout: float | None = None,
) -> None:
    WebDriverWait(driver, timeout or DEFAULT_TIMEOUT_SEC).until(
        EC.visibility_of_element_located(locator)
    )


def wait_present(
    driver: WebDriver,
    locator: tuple[str, str],
    timeout: float | None = None,
) -> None:
    WebDriverWait(driver, timeout or DEFAULT_TIMEOUT_SEC).until(
        EC.presence_of_element_located(locator)
    )


def wait_hidden(
    driver: WebDriver,
    locator: tuple[str, str],
    timeout: float | None = None,
) -> None:
    WebDriverWait(driver, timeout or DEFAULT_TIMEOUT_SEC).until(
        EC.invisibility_of_element_located(locator)
    )


def wait_for_clerk_ready(driver: WebDriver, timeout: float | None = None) -> None:
    wait_present(driver, _CLERK_READY, timeout)


def left_auth_url(driver: WebDriver, auth_path: str) -> bool:
    """Return whether the browser has left an auth URL (including factor-two)."""
    url = driver.current_url
    return auth_path not in url and "factor-two" not in url


def wait_until_element_displayed(
    driver: WebDriver,
    resolver: Callable[[], object],
    timeout: float | None = None,
) -> None:
    """Wait until ``resolver()`` returns a displayed element."""
    t = timeout or DEFAULT_TIMEOUT_SEC

    def _ready(_driver: WebDriver) -> bool:
        try:
            return resolver().is_displayed()
        except Exception:
            return False

    WebDriverWait(driver, t).until(_ready)

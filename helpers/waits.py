"""Selenium wait helpers for Clerk auth flows."""

from __future__ import annotations

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

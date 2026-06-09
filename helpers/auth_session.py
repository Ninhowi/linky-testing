"""Login helpers for tests that require an authenticated session."""

from __future__ import annotations

import os

import pytest
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from pages.sign_in import SignInPage

_SIGN_IN_PATH = "/sign-in"
_LOGIN_WAIT_TIMEOUT_SEC = 25.0


def require_env_credentials() -> tuple[str, str, str | None]:
    """Return ``(email, password, otp)`` from env or skip the test."""
    email = os.environ.get("USER_EMAIL", "").strip()
    password = os.environ.get("USER_PASSWORD", "").strip()
    otp_raw = os.environ.get("USER_OTP", "").strip()
    otp = otp_raw or None

    if not email or not password:
        pytest.skip("USER_EMAIL and USER_PASSWORD are required for profile tests")
    return email, password, otp


def login_with_env_credentials(driver: WebDriver, base_url: str) -> None:
    """Sign in using ``USER_EMAIL``, ``USER_PASSWORD``, and optional ``USER_OTP``."""
    email, password, otp = require_env_credentials()
    page = SignInPage.open(driver, base_url)
    page.identifier.submit_email(email)
    page.password.wait_until_visible()
    page.password.submit_password(password)

    if otp:
        page.otp.wait_until_visible()
        page.otp.fill_otp(otp)

    def _left_sign_in(drv: WebDriver) -> bool:
        url = drv.current_url
        return _SIGN_IN_PATH not in url and "factor-two" not in url

    WebDriverWait(driver, _LOGIN_WAIT_TIMEOUT_SEC).until(_left_sign_in)

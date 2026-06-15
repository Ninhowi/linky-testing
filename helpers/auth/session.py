"""Login helpers for authenticated profile tests.

Hàm hỗ trợ đăng nhập cho test profile đã xác thực.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from helpers.browser.e2e_session import inject_e2e_key
from helpers.browser.waits import left_auth_url
from pages.sign_in import SignInPage

_SIGN_IN_PATH = "/sign-in"
_LOGIN_WAIT_TIMEOUT_SEC = 25.0


@dataclass(frozen=True, slots=True)
class Credentials:
    email: str
    password: str
    otp: str | None = None

    def assert_valid(self, *, reason: str = "email and password are required") -> None:
        if not self.email or not self.password:
            pytest.skip(reason)


@dataclass
class AuthSessionState:
    active_base_url: str | None = None


def require_env_credentials() -> Credentials:
    """Return credentials from env or skip the test.

    Trả về credentials từ env hoặc bỏ qua test.
    """
    email = os.environ.get("USER_EMAIL", "").strip()
    password = os.environ.get("USER_PASSWORD", "").strip()
    otp_raw = os.environ.get("USER_OTP", "").strip()
    credentials = Credentials(email=email, password=password, otp=otp_raw or None)
    credentials.assert_valid(reason="USER_EMAIL and USER_PASSWORD are required")
    return credentials


def require_env_credentials_user2() -> Credentials:
    """Return second-user credentials from env or skip the test.

    Trả về credentials người dùng thứ hai từ env hoặc bỏ qua test.
    """
    email = os.environ.get("USER2_EMAIL", "").strip()
    password = os.environ.get("USER2_PASSWORD", "").strip()
    otp_raw = os.environ.get("USER2_OTP", "").strip()
    credentials = Credentials(email=email, password=password, otp=otp_raw or None)
    credentials.assert_valid(reason="USER2_EMAIL and USER2_PASSWORD are required")
    return credentials


def login_with_env_credentials(driver: WebDriver, base_url: str) -> None:
    """Sign in using ``USER_EMAIL``, ``USER_PASSWORD``, and optional ``USER_OTP``.

    When ``USER_OTP`` is unset and Clerk asks for a code, OTP is read from stdin.

    Đăng nhập bằng ``USER_EMAIL``, ``USER_PASSWORD`` và ``USER_OTP`` tùy chọn.
    Nếu thiếu ``USER_OTP`` mà Clerk yêu cầu mã, OTP được đọc từ stdin.
    """
    login_with_credentials(driver, base_url, require_env_credentials())


def _prompt_otp() -> str:
    print("Enter OTP:", file=sys.stderr, flush=True)
    return input().strip()


def _resolve_otp(credentials: Credentials) -> str:
    if credentials.otp:
        return credentials.otp
    return _prompt_otp()


def _submit_otp_if_required(
    driver: WebDriver, page: SignInPage, credentials: Credentials
) -> None:
    def _otp_or_signed_in(_driver: WebDriver) -> str | None:
        if left_auth_url(_driver, _SIGN_IN_PATH):
            return "signed_in"
        try:
            if page.otp.otp_input().is_displayed():
                return "otp"
        except Exception:
            pass
        return None

    try:
        outcome = WebDriverWait(driver, _LOGIN_WAIT_TIMEOUT_SEC).until(_otp_or_signed_in)
    except TimeoutException:
        return

    if outcome != "otp":
        return

    page.otp.fill_otp(_resolve_otp(credentials))


def ensure_logged_in_for_base_url(
    driver: WebDriver,
    base_url: str,
    credentials: Credentials,
    state: AuthSessionState,
) -> None:
    """Sign in only when ``base_url`` differs from the active session environment.

    Chỉ đăng nhập khi ``base_url`` khác môi trường session hiện tại.
    """
    normalized = base_url.rstrip("/")
    if state.active_base_url == normalized:
        return
    inject_e2e_key(driver, normalized)
    login_with_credentials(driver, normalized, credentials)
    state.active_base_url = normalized


def login_with_credentials(driver: WebDriver, base_url: str, credentials: Credentials) -> None:
    """Sign in using credentials.

    Đăng nhập bằng credentials.
    """
    page = SignInPage.open(driver, base_url)
    page.identifier.submit_email(credentials.email)
    page.password.wait_until_visible()
    page.password.submit_password(credentials.password)

    _submit_otp_if_required(driver, page, credentials)
    _wait_until_left_sign_in(driver)


def _wait_until_left_sign_in(driver: WebDriver) -> None:
    WebDriverWait(driver, _LOGIN_WAIT_TIMEOUT_SEC).until(
        lambda d: left_auth_url(d, _SIGN_IN_PATH)
    )

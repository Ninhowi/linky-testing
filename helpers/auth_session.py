"""Login helpers and saved auth state (cookies + web storage) for authenticated tests."""

from __future__ import annotations

import os
from typing import Any, TypedDict

import pytest
from selenium.common.exceptions import InvalidCookieDomainException, WebDriverException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from pages.sign_in import SignInPage

_SIGN_IN_PATH = "/sign-in"
_LOGIN_WAIT_TIMEOUT_SEC = 25.0
_AUTH_READY_TIMEOUT_SEC = 20.0

_ALLOWED_COOKIE_KEYS = frozenset(
    {"name", "value", "domain", "path", "expiry", "secure", "httpOnly", "sameSite"}
)

_CAPTURE_STORAGE_JS = """
const localStorageData = {};
for (let index = 0; index < localStorage.length; index += 1) {
    const key = localStorage.key(index);
    localStorageData[key] = localStorage.getItem(key);
}
const sessionStorageData = {};
for (let index = 0; index < sessionStorage.length; index += 1) {
    const key = sessionStorage.key(index);
    sessionStorageData[key] = sessionStorage.getItem(key);
}
return {localStorage: localStorageData, sessionStorage: sessionStorageData};
"""

_RESTORE_STORAGE_JS = """
const localStorageData = arguments[0];
const sessionStorageData = arguments[1];
for (const [key, value] of Object.entries(localStorageData)) {
    localStorage.setItem(key, value);
}
for (const [key, value] of Object.entries(sessionStorageData)) {
    sessionStorage.setItem(key, value);
}
"""


class AuthState(TypedDict):
    base_url: str
    cookies: list[dict[str, Any]]
    local_storage: dict[str, str]
    session_storage: dict[str, str]


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

    _wait_until_left_sign_in(driver)


def _wait_until_left_sign_in(driver: WebDriver) -> None:
    def _left_sign_in(drv: WebDriver) -> bool:
        url = drv.current_url
        return _SIGN_IN_PATH not in url and "factor-two" not in url

    WebDriverWait(driver, _LOGIN_WAIT_TIMEOUT_SEC).until(_left_sign_in)


def _sanitize_cookie(cookie: dict[str, Any]) -> dict[str, Any]:
    cleaned = {key: cookie[key] for key in _ALLOWED_COOKIE_KEYS if key in cookie}
    expiry = cleaned.get("expiry")
    if expiry is not None:
        cleaned["expiry"] = int(expiry)
    same_site = cleaned.get("sameSite")
    if same_site is not None and same_site not in ("Strict", "Lax", "None"):
        cleaned.pop("sameSite", None)
    return cleaned


def capture_auth_state(driver: WebDriver, base_url: str) -> AuthState:
    """Persist cookies and web storage after a successful login."""
    _wait_until_left_sign_in(driver)
    normalized = base_url.rstrip("/")
    driver.get(normalized)
    storage = driver.execute_script(_CAPTURE_STORAGE_JS)
    return AuthState(
        base_url=normalized,
        cookies=driver.get_cookies(),
        local_storage=storage.get("localStorage", {}),
        session_storage=storage.get("sessionStorage", {}),
    )


def _add_cookie(driver: WebDriver, cookie: dict[str, Any]) -> None:
    sanitized = _sanitize_cookie(cookie)
    try:
        driver.add_cookie(sanitized)
    except InvalidCookieDomainException:
        fallback = {key: sanitized[key] for key in ("name", "value", "path", "secure", "httpOnly") if key in sanitized}
        driver.add_cookie(fallback)
    except WebDriverException:
        pass


def restore_auth_state(driver: WebDriver, state: AuthState) -> None:
    """Apply saved cookies and web storage to ``driver``."""
    base_url = state["base_url"]
    driver.get(base_url)
    for cookie in state["cookies"]:
        _add_cookie(driver, cookie)
    driver.get(base_url)
    driver.execute_script(
        _RESTORE_STORAGE_JS,
        state["local_storage"],
        state["session_storage"],
    )
    driver.get(base_url)


def wait_until_authenticated(
    driver: WebDriver,
    base_url: str,
    *,
    path: str = "/user/profile",
) -> None:
    """Open ``path`` and wait until Clerk no longer redirects to sign-in."""
    driver.get(f"{base_url.rstrip('/')}{path}")

    def _authenticated(drv: WebDriver) -> bool:
        return _SIGN_IN_PATH not in drv.current_url and "factor-two" not in drv.current_url

    WebDriverWait(driver, _AUTH_READY_TIMEOUT_SEC).until(_authenticated)

from __future__ import annotations

import os
import pytest

from cloakbrowser.config import get_default_stealth_args
from cloakbrowser.download import ensure_binary
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from helpers.auth.session import (
    AuthSessionState,
    Credentials,
    ensure_logged_in_for_base_url,
    require_env_credentials,
    require_env_credentials_user2,
)
from helpers.call.session import setup_matched_call
from helpers.browser.viewport import CHAT_VIEWPORT_LAYOUTS, apply_viewport_layout, parse_viewport_layout
from helpers.runtime.env import load_env

load_env()

def _base_url() -> str | None:
    url = os.environ.get("BASE_TEST_URL", "").rstrip("/")
    return url or None

def _headed() -> bool:
    return os.environ.get("HEADED", "").lower() in ("1", "true", "yes")

@pytest.fixture(scope="session")
def base_url() -> str:
    url = _base_url()
    if not url:
        pytest.skip("BASE_TEST_URL is not set")
    return url

def _apply_media_options(options: Options) -> None:
    options.add_argument("--use-fake-device-for-media-stream")
    options.add_argument("--use-fake-ui-for-media-stream")
    prefs = dict(options.experimental_options.get("prefs", {}))
    prefs.update(
        {
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.media_stream_mic": 1,
        }
    )
    options.experimental_options["prefs"] = prefs

def _create_driver(*, media: bool = False) -> webdriver.Chrome:
    binary_path = ensure_binary()
    options = Options()
    options.binary_location = binary_path
    for arg in get_default_stealth_args():
        options.add_argument(arg)
    if not _headed():
        options.add_argument("--headless=new")
    if os.environ.get("IGNORE_HTTPS_ERRORS", "").lower() in ("1", "true", "yes"):
        options.add_argument("--ignore-certificate-errors")
    options.add_argument("--window-size=1280,720")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    if media:
        _apply_media_options(options)
    drv = webdriver.Chrome(service=Service(), options=options)
    drv.set_window_size(1280, 720)
    drv.implicitly_wait(0)
    return drv

@pytest.fixture
def driver():
    drv = _create_driver()
    yield drv
    drv.quit()

@pytest.fixture(scope="module")
def _profile_auth_state() -> AuthSessionState:
    return AuthSessionState()


@pytest.fixture(scope="module")
def _profile_browser():
    drv = _create_driver()
    yield drv
    drv.quit()


@pytest.fixture
def credentials_driver(
    _profile_browser,
    _profile_auth_state,
    base_url: str,
    credentials: Credentials | None = None,
):
    """Shared browser for profile tests; signs in once per ``base_url``.

    Trình duyệt dùng chung cho test profile; đăng nhập một lần mỗi ``base_url``.
    """
    creds = require_env_credentials() if credentials is None else credentials
    creds.assert_valid(reason="USER_EMAIL and USER_PASSWORD are required")
    ensure_logged_in_for_base_url(_profile_browser, base_url, creds, _profile_auth_state)
    return _profile_browser


@pytest.fixture(scope="module")
def _call_auth_state() -> AuthSessionState:
    return AuthSessionState()


@pytest.fixture(scope="module")
def _call_browser():
    drv = _create_driver(media=True)
    yield drv
    drv.quit()


@pytest.fixture
def call_credentials_driver(
    _call_browser,
    _call_auth_state,
    base_url: str,
):
    """Shared browser for single-profile call tests; signs in once per ``base_url``.

    Trình duyệt dùng chung cho test call một profile; đăng nhập một lần mỗi ``base_url``.
    """
    creds = require_env_credentials()
    ensure_logged_in_for_base_url(_call_browser, base_url, creds, _call_auth_state)
    return _call_browser


@pytest.fixture(scope="module")
def _call_user1_auth_state() -> AuthSessionState:
    return AuthSessionState()


@pytest.fixture(scope="module")
def _call_user2_auth_state() -> AuthSessionState:
    return AuthSessionState()


@pytest.fixture(scope="module")
def call_user1_driver(_call_user1_auth_state, base_url: str):
    drv = _create_driver(media=True)
    creds = require_env_credentials()
    ensure_logged_in_for_base_url(drv, base_url, creds, _call_user1_auth_state)
    yield drv
    drv.quit()


@pytest.fixture(scope="module")
def call_user2_driver(_call_user2_auth_state, base_url: str):
    drv = _create_driver(media=True)
    creds = require_env_credentials_user2()
    ensure_logged_in_for_base_url(drv, base_url, creds, _call_user2_auth_state)
    yield drv
    drv.quit()


@pytest.fixture(scope="module", params=CHAT_VIEWPORT_LAYOUTS)
def chat_viewport(request: pytest.FixtureRequest) -> str:
    return str(request.param)


@pytest.fixture(scope="module")
def chat_viewport_users(chat_viewport: str) -> tuple[str, str]:
    return parse_viewport_layout(chat_viewport)


@pytest.fixture(scope="module")
def in_call_chat_pair(
    call_user1_driver,
    call_user2_driver,
    base_url: str,
    chat_viewport: str,
):
    """Two browsers matched once per viewport layout for the in-call chat module.

    Hai trình duyệt ghép cặp một lần mỗi bố cục viewport cho module chat in_call.
    """
    apply_viewport_layout(call_user1_driver, call_user2_driver, chat_viewport)

    creds_a = require_env_credentials()
    creds_b = require_env_credentials_user2()
    page_a, page_b = setup_matched_call(
        call_user1_driver,
        call_user2_driver,
        base_url,
        creds_a,
        creds_b,
    )
    yield page_a, page_b
    for page in (page_a, page_b):
        try:
            page.ensure_idle()
        except Exception:
            pass


@pytest.fixture
def matched_call_pair(
    call_user1_driver,
    call_user2_driver,
    base_url: str,
):
    """Two authenticated browsers matched in an active call.

    Hai trình duyệt đã xác thực được ghép cặp trong cuộc gọi.
    """
    creds_a = require_env_credentials()
    creds_b = require_env_credentials_user2()
    page_a, page_b = setup_matched_call(
        call_user1_driver,
        call_user2_driver,
        base_url,
        creds_a,
        creds_b,
    )
    yield page_a, page_b
    for page in (page_a, page_b):
        try:
            page.ensure_idle()
        except Exception:
            pass

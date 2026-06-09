from __future__ import annotations

import os

import pytest
from cloakbrowser.config import get_default_stealth_args
from cloakbrowser.download import ensure_binary
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from helpers.auth_session import (
    AuthState,
    capture_auth_state,
    login_with_env_credentials,
    require_env_credentials,
    restore_auth_state,
    wait_until_authenticated,
)
from helpers.env import load_env
from pages.user_profile import UserProfilePage

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


def _create_driver() -> webdriver.Chrome:
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

    drv = webdriver.Chrome(service=Service(), options=options)
    drv.set_window_size(1280, 720)
    drv.implicitly_wait(0)
    return drv


@pytest.fixture
def driver():
    drv = _create_driver()
    yield drv
    drv.quit()


@pytest.fixture(scope="session")
def auth_state(base_url: str) -> AuthState:
    """Sign in once per test run and save cookies + web storage for reuse."""
    require_env_credentials()
    drv = _create_driver()
    try:
        login_with_env_credentials(drv, base_url)
        return capture_auth_state(drv, base_url)
    finally:
        drv.quit()


@pytest.fixture(scope="module")
def profile_driver(base_url: str, auth_state: AuthState):
    """Browser session restored from ``auth_state``, shared across profile tests."""
    drv = _create_driver()
    try:
        restore_auth_state(drv, auth_state)
        wait_until_authenticated(drv, base_url, path=UserProfilePage.PATH)
        UserProfilePage.wait_until_ready(drv)
        yield drv
    finally:
        drv.quit()

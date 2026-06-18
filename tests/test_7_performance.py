from __future__ import annotations

import os
import time

import pytest
from selenium.webdriver.support.ui import WebDriverWait

from helpers.auth.session import (
    require_env_credentials,
    require_env_credentials_user2,
)
from helpers.browser.waits import left_auth_url
from helpers.call.session import setup_matched_call
from helpers.performance import assert_performance, measure_seconds
from pages.sign_in import SignInPage
from pages.sign_up import SignUpPage
from pages.user_profile import UserProfilePage
from pages.video_chat import VideoChatPage


pytestmark = pytest.mark.performance


DEFAULT_SIGN_UP_PASSWORD = os.environ.get(
    "PERF_SIGN_UP_PASSWORD",
    "Performance12@34",
)


def _threshold(name: str, default: float) -> float:
    """Allow overriding threshold from environment variables."""
    raw = os.environ.get(name)
    if not raw:
        return default
    return float(raw)


def _unique_clerk_email() -> str:
    """
    Create a unique Clerk test email.

    Preferred domain:
    1. PERF_EMAIL_DOMAIN
    2. domain from USER_EMAIL
    3. example.com
    """
    domain = os.environ.get("PERF_EMAIL_DOMAIN", "").strip()
    if not domain:
        user_email = os.environ.get("USER_EMAIL", "").strip()
        if "@" in user_email:
            domain = user_email.split("@", 1)[1]
    domain = domain or "example.com"

    millis = int(time.time() * 1000)
    return f"perf{millis}+clerk_test@{domain}"


def _wait_left_auth(driver, auth_path: str, timeout: float) -> None:
    WebDriverWait(driver, timeout).until(lambda d: left_auth_url(d, auth_path))


def test_perf_su_01_sign_up_page_load(driver, base_url: str) -> None:
    """
    PF-SU-01:
    Measure sign-up page load time until the sign-up form is visible.
    """
    page_holder: dict[str, SignUpPage] = {}

    def action() -> None:
        page_holder["page"] = SignUpPage.open(driver, base_url)

    duration = measure_seconds(action)

    assert_performance(
        test_id="PF-SU-01",
        feature="Sign Up",
        metric="Sign-up page load time",
        duration=duration,
        threshold=_threshold("PERF_THRESHOLD_SIGN_UP_LOAD", 5),
    )


def test_perf_su_02_valid_sign_up_submit_to_otp(driver, base_url: str) -> None:
    """
    PF-SU-02:
    Measure valid sign-up submit time until OTP screen is visible.
    """
    page = SignUpPage.open(driver, base_url)

    def action() -> None:
        page.submit_registration(
            _unique_clerk_email(),
            DEFAULT_SIGN_UP_PASSWORD,
            accept_legal=True,
        )
        page.otp.wait_until_visible(timeout=20)

    duration = measure_seconds(action)

    assert_performance(
        test_id="PF-SU-02",
        feature="Sign Up",
        metric="Valid sign-up submit to OTP time",
        duration=duration,
        threshold=_threshold("PERF_THRESHOLD_SIGN_UP_SUBMIT", 20),
    )


def test_perf_si_01_sign_in_page_load(driver, base_url: str) -> None:
    """
    PF-SI-01:
    Measure sign-in page load time until identifier field is visible.
    """

    def action() -> None:
        SignInPage.open(driver, base_url)

    duration = measure_seconds(action)

    assert_performance(
        test_id="PF-SI-01",
        feature="Sign In",
        metric="Sign-in page load time",
        duration=duration,
        threshold=_threshold("PERF_THRESHOLD_SIGN_IN_LOAD", 5),
    )


def test_perf_si_02_valid_sign_in_to_authenticated_page(driver, base_url: str) -> None:
    """
    PF-SI-02:
    Measure valid sign-in time from email submit to authenticated redirect.
    """
    credentials = require_env_credentials()
    page = SignInPage.open(driver, base_url)

    def action() -> None:
        page.identifier.submit_email(credentials.email)
        page.password.wait_until_visible()
        page.password.submit_password(credentials.password)

        try:
            page.otp.wait_until_visible(timeout=5)
            if credentials.otp:
                page.otp.fill_otp(credentials.otp)
        except Exception:
            pass

        _wait_left_auth(driver, "/sign-in", timeout=25)

    duration = measure_seconds(action)

    assert_performance(
        test_id="PF-SI-02",
        feature="Sign In",
        metric="Valid sign-in total time",
        duration=duration,
        threshold=_threshold("PERF_THRESHOLD_SIGN_IN_TOTAL", 25),
    )


def test_perf_pr_01_profile_page_load(credentials_driver, base_url: str) -> None:
    """
    PF-PR-01:
    Measure profile page load time until all profile sections are ready.
    """

    def action() -> None:
        UserProfilePage.open(credentials_driver, base_url)

    duration = measure_seconds(action)

    assert_performance(
        test_id="PF-PR-01",
        feature="Profile",
        metric="Profile page load time",
        duration=duration,
        threshold=_threshold("PERF_THRESHOLD_PROFILE_LOAD", 8),
    )


def test_perf_pr_02_edit_profile_bio(credentials_driver, base_url: str) -> None:
    """
    PF-PR-02:
    Measure time to edit and save the Bio section.
    """
    page = UserProfilePage.open(credentials_driver, base_url)
    new_bio = f"Performance bio {int(time.time())}"

    def action() -> None:
        page.edit_section("bio")
        page.fill_fields("bio", [("bio", new_bio)])
        page.click_save_section("bio")
        page.wait_save_section("bio")

    duration = measure_seconds(action)

    assert_performance(
        test_id="PF-PR-02",
        feature="Profile",
        metric="Edit profile bio save time",
        duration=duration,
        threshold=_threshold("PERF_THRESHOLD_PROFILE_SAVE", 10),
    )


def test_perf_vc_01_call_page_load(call_credentials_driver, base_url: str) -> None:
    """
    PF-VC-01:
    Measure /call page load time until idle call UI is visible.
    """

    def action() -> None:
        VideoChatPage.open(call_credentials_driver, base_url)

    duration = measure_seconds(action)

    assert_performance(
        test_id="PF-VC-01",
        feature="Video Call",
        metric="Call page load time",
        duration=duration,
        threshold=_threshold("PERF_THRESHOLD_CALL_LOAD", 10),
    )


def test_perf_vc_02_start_search_to_searching(call_credentials_driver, base_url: str) -> None:
    """
    PF-VC-02:
    Measure time from clicking Start to entering searching state.
    """
    page = VideoChatPage.open(call_credentials_driver, base_url)

    try:
        def action() -> None:
            page.start_search()

        duration = measure_seconds(action)

        assert_performance(
            test_id="PF-VC-02",
            feature="Video Call",
            metric="Start search to searching state time",
            duration=duration,
            threshold=_threshold("PERF_THRESHOLD_CALL_SEARCH", 5),
        )
    finally:
        page.ensure_idle()


def test_perf_vc_03_two_users_match_to_in_call(
    call_user1_driver,
    call_user2_driver,
    base_url: str,
) -> None:
    """
    PF-VC-03:
    Measure time for two authenticated users to match and enter an active call.
    """
    credentials_a = require_env_credentials()
    credentials_b = require_env_credentials_user2()
    pages: tuple[VideoChatPage, VideoChatPage] | None = None

    try:
        def action() -> None:
            nonlocal pages
            pages = setup_matched_call(
                call_user1_driver,
                call_user2_driver,
                base_url,
                credentials_a,
                credentials_b,
                match_timeout=120,
            )

        duration = measure_seconds(action)

        assert_performance(
            test_id="PF-VC-03",
            feature="Video Call",
            metric="Two users match to in-call time",
            duration=duration,
            threshold=_threshold("PERF_THRESHOLD_CALL_MATCH", 120),
        )
    finally:
        if pages:
            for page in pages:
                try:
                    page.ensure_idle()
                except Exception:
                    pass

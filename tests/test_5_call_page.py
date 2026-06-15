"""Call page cases for ``/call`` (smoke + integration core).

Test trang ``/call`` — smoke một profile và integration hai profile.
"""

from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from helpers.browser.waits import DEFAULT_TIMEOUT_SEC
from pages.selectors.video_chat import (
    CALL_HISTORY_PAGE,
    CALL_HISTORY_TABLE,
    CHAT_IDLE_PROGRESS_CARD,
    CHAT_START_BUTTON,
    CHAT_VIDEO_CONTAINER,
)
from pages.video_chat import VideoChatPage

pytestmark = [
    pytest.mark.call,
    pytest.mark.xdist_group("call"),
]


class TestCallPageSmoke:
    pytestmark = pytest.mark.call_smoke

    def test_reaches_call_idle(
        self,
        call_credentials_driver,
        base_url: str,
    ) -> None:
        page = VideoChatPage.open(call_credentials_driver, base_url)
        assert page.is_idle_container_visible()
        assert "/call" in call_credentials_driver.current_url

    def test_idle_shell_elements(
        self,
        call_credentials_driver,
        base_url: str,
    ) -> None:
        page = VideoChatPage.open(call_credentials_driver, base_url)
        assert page.is_element_visible(CHAT_START_BUTTON)
        assert page.is_element_visible(CHAT_VIDEO_CONTAINER)
        assert page.is_element_visible(CHAT_IDLE_PROGRESS_CARD)
        assert not page.is_timer_visible()

    def test_start_search_shows_searching(
        self,
        call_credentials_driver,
        base_url: str,
    ) -> None:
        page = VideoChatPage.open(call_credentials_driver, base_url)
        page.start_search()
        assert page.get_connection_status() == "searching"
        page.cancel_search()

    def test_cancel_search_returns_idle(
        self,
        call_credentials_driver,
        base_url: str,
    ) -> None:
        page = VideoChatPage.open(call_credentials_driver, base_url)
        page.start_search()
        page.cancel_search()
        assert page.is_post_call_idle_status()
        assert page.is_idle_container_visible()

    def test_local_preview_after_start(
        self,
        call_credentials_driver,
        base_url: str,
    ) -> None:
        page = VideoChatPage.open(call_credentials_driver, base_url)
        page.start_search()
        assert page.is_local_video_visible()
        page.cancel_search()

    def test_navigate_call_history(
        self,
        call_credentials_driver,
        base_url: str,
    ) -> None:
        page = VideoChatPage.open(call_credentials_driver, base_url)
        page.open_sidebar_nav("callHistory")
        assert "/call/history" in call_credentials_driver.current_url
        assert page.is_call_history_page_visible()

    def test_call_history_table_and_refresh(
        self,
        call_credentials_driver,
        base_url: str,
    ) -> None:
        page = VideoChatPage.open(call_credentials_driver, base_url)
        page.open_sidebar_nav("callHistory")
        assert page.is_element_visible(CALL_HISTORY_TABLE)
        page.refresh_call_history()
        assert page.is_element_visible(CALL_HISTORY_PAGE)

    def test_navigate_back_to_video_chat(
        self,
        call_credentials_driver,
        base_url: str,
    ) -> None:
        page = VideoChatPage.open(call_credentials_driver, base_url)
        page.open_sidebar_nav("callHistory")
        page.open_sidebar_nav("videoChat")
        assert call_credentials_driver.current_url.rstrip("/").endswith("/call")
        page.wait_until_ready()
        assert page.is_idle_container_visible()


class TestCallPageIntegration:
    pytestmark = pytest.mark.call_integration

    def test_two_user_match(self, matched_call_pair) -> None:
        page_a, page_b = matched_call_pair
        assert page_a.get_connection_status() == "in_call"
        assert page_b.get_connection_status() == "in_call"
        assert page_a.is_remote_video_visible()
        assert page_b.is_remote_video_visible()
        assert page_a.is_timer_visible()
        assert page_b.is_timer_visible()

    def test_mute_unmute_local(self, matched_call_pair) -> None:
        page_a, _page_b = matched_call_pair
        call_settings = page_a.get_user_call_settings()
        default_muted = bool(call_settings.get("default_mute_mic", False))
        assert page_a.is_mute_destructive() == default_muted
        page_a.toggle_mute()
        WebDriverWait(page_a._driver, DEFAULT_TIMEOUT_SEC).until(
            lambda _driver: page_a.is_mute_destructive() != default_muted
        )
        page_a.toggle_mute()
        WebDriverWait(page_a._driver, DEFAULT_TIMEOUT_SEC).until(
            lambda _driver: page_a.is_mute_destructive() == default_muted
        )

    def test_camera_off_on_local(self, matched_call_pair) -> None:
        page_a, _page_b = matched_call_pair
        call_settings = page_a.get_user_call_settings()
        camera_starts_off = bool(call_settings.get("default_disable_camera", False))
        assert page_a.is_camera_off_indicator_visible() == camera_starts_off
        page_a.toggle_video()
        WebDriverWait(page_a._driver, DEFAULT_TIMEOUT_SEC).until(
            lambda _driver: page_a.is_camera_off_indicator_visible()
            != camera_starts_off
        )
        page_a.toggle_video()
        WebDriverWait(page_a._driver, DEFAULT_TIMEOUT_SEC).until(
            lambda _driver: page_a.is_camera_off_indicator_visible() == camera_starts_off
        )

    def test_end_call_returns_idle_both(self, matched_call_pair) -> None:
        page_a, page_b = matched_call_pair
        page_a.end_call()
        page_b.wait_post_call_idle()
        assert page_a.is_idle_container_visible()
        assert page_b.is_idle_container_visible()
        assert page_a.is_post_call_idle_status()
        assert page_b.is_post_call_idle_status()

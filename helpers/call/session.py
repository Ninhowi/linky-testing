"""Two-user call setup helpers.

Hàm thiết lập cuộc gọi hai người dùng.
"""

from __future__ import annotations

import time

from selenium.webdriver.remote.webdriver import WebDriver

from helpers.auth.session import Credentials
from helpers.browser.waits import wait_for_socket_ready
from pages.video_chat import VideoChatPage

_MATCH_TIMEOUT_SEC = 120.0
_SEARCH_STAGGER_SEC = 2.0


def setup_matched_call(
    driver_a: WebDriver,
    driver_b: WebDriver,
    base_url: str,
    creds_a: Credentials,
    creds_b: Credentials,
    *,
    match_timeout: float = _MATCH_TIMEOUT_SEC,
) -> tuple[VideoChatPage, VideoChatPage]:
    """Log in both drivers, match on ``/call``, and wait until both are in-call.

    Đăng nhập cả hai driver, ghép cặp trên ``/call``, chờ cả hai vào cuộc gọi.
    """
    del creds_a, creds_b

    page_a = VideoChatPage(driver_a, base_url)
    page_b = VideoChatPage(driver_b, base_url)

    page_a.prepare_call_page()
    page_b.prepare_call_page()

    page_a.start_search()
    time.sleep(_SEARCH_STAGGER_SEC)
    page_b.start_search()

    try:
        page_a.wait_in_call(timeout=match_timeout)
        page_b.wait_in_call(timeout=match_timeout)
    except Exception as exc:
        status_a = page_a.get_connection_status()
        status_b = page_b.get_connection_status()
        raise RuntimeError(
            f"Match failed: user_a={status_a!r}, user_b={status_b!r}"
        ) from exc

    return page_a, page_b

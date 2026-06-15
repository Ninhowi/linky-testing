"""Video chat page at ``/call``.

Trang video chat tại ``/call``.
"""

from __future__ import annotations

import json
import time

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from helpers.browser.viewport import MOBILE_BREAKPOINT_PX
from helpers.browser.waits import DEFAULT_TIMEOUT_SEC, wait_for_socket_ready, wait_visible
from helpers.call.chat_validation import call_chat_message_chunks
from pages.selectors.video_chat import (
    CALL_HISTORY_PAGE,
    CALL_HISTORY_REFRESH_BUTTON,
    CALL_HISTORY_TABLE,
    CHAT_CALL_TIMER,
    CHAT_CAMERA_OFF_INDICATOR,
    CHAT_CANCEL_SEARCH_BUTTON,
    CHAT_CONTROLS_BAR,
    CHAT_END_CALL_BUTTON,
    CHAT_FULL_PAGE,
    CHAT_FULL_PAGE_CLIENT,
    CHAT_IDLE_CONTAINER,
    CHAT_INPUT,
    CHAT_LOCAL_VIDEO,
    CHAT_MESSAGES_CONTAINER,
    CHAT_MUTE_BUTTON,
    CHAT_OVERFLOW_MENU_BUTTON,
    CHAT_REMOTE_VIDEO,
    CHAT_SEARCHING_INDICATOR,
    CHAT_SEND_BUTTON,
    CHAT_SIDEBAR,
    CHAT_SIDEBAR_SHEET,
    CHAT_START_BUTTON,
    CHAT_TOGGLE_BUTTON,
    CHAT_VIDEO_CONTAINER,
    CHAT_VIDEO_TOGGLE_BUTTON,
    SIDEBAR_CALL_HISTORY,
    SIDEBAR_VIDEO_CHAT,
    SIDEBAR_TRIGGER,
    sidebar_nav,
    sidebar_sub_parent,
)

_CALL_READY_TIMEOUT_SEC = 30.0
_MATCH_TIMEOUT_SEC = 60.0
_UI_SETTLE_SEC = 0.3


def _click(driver: WebDriver, element: WebElement) -> None:
    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
        element,
    )
    time.sleep(_UI_SETTLE_SEC)


def _native_click(driver: WebDriver, element: WebElement) -> None:
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    element.click()
    time.sleep(_UI_SETTLE_SEC)


def _click_nav_link(driver: WebDriver, element: WebElement) -> None:
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    element.click()
    time.sleep(_UI_SETTLE_SEC)


_NAV_URL_PARTS: dict[str, str] = {
    "videoChat": "/call",
    "callHistory": "/call/history",
}

_NAV_READY_SELECTORS: dict[str, str] = {
    "videoChat": CHAT_IDLE_CONTAINER,
    "callHistory": CALL_HISTORY_PAGE,
}


class VideoChatPage:
    PATH = "/call"
    CHAT_PATH = "/call/chat"
    HISTORY_PATH = "/call/history"

    def __init__(self, driver: WebDriver, base_url: str | None = None) -> None:
        self._driver = driver
        self._base_url = base_url.rstrip("/") if base_url else None

    @classmethod
    def open(cls, driver: WebDriver, base_url: str) -> VideoChatPage:
        page = cls(driver, base_url)
        driver.get(f"{base_url.rstrip('/')}{cls.PATH}")
        page.wait_until_ready()
        return page

    def wait_until_ready(self, timeout: float | None = None) -> None:
        deadline = timeout or _CALL_READY_TIMEOUT_SEC
        wait_visible(self._driver, (By.CSS_SELECTOR, CHAT_IDLE_CONTAINER), deadline)
        wait_visible(self._driver, (By.CSS_SELECTOR, CHAT_START_BUTTON), deadline)

    def prepare_call_page(self) -> None:
        if self._base_url:
            self._driver.get(f"{self._base_url}{self.PATH}")
        self.wait_until_ready()
        wait_for_socket_ready(self._driver, _CALL_READY_TIMEOUT_SEC)

    def start_search(self) -> None:
        wait_for_socket_ready(self._driver, _CALL_READY_TIMEOUT_SEC)
        button = self._driver.find_element(By.CSS_SELECTOR, CHAT_START_BUTTON)
        _click(self._driver, button)
        wait_visible(
            self._driver,
            (By.CSS_SELECTOR, CHAT_SEARCHING_INDICATOR),
            _CALL_READY_TIMEOUT_SEC,
        )

    def get_connection_status(self) -> str | None:
        try:
            element = self._driver.find_element(By.CSS_SELECTOR, CHAT_VIDEO_CONTAINER)
        except NoSuchElementException:
            return None
        return element.get_attribute("data-connection-status")

    def wait_user_settings(self, timeout: float | None = None) -> dict:
        deadline = timeout or DEFAULT_TIMEOUT_SEC

        def _loaded(_driver: WebDriver) -> dict | bool:
            try:
                element = _driver.find_element(By.CSS_SELECTOR, CHAT_VIDEO_CONTAINER)
            except NoSuchElementException:
                return False
            raw = element.get_attribute("data-user-settings")
            if not raw:
                return False
            return json.loads(raw)

        result = WebDriverWait(self._driver, deadline).until(_loaded)
        return result if isinstance(result, dict) else {}

    def get_user_call_settings(self) -> dict:
        settings = self.wait_user_settings()
        call = settings.get("call")
        return call if isinstance(call, dict) else {}

    def is_mobile_viewport(self) -> bool:
        return self._driver.get_window_size()["width"] < MOBILE_BREAKPOINT_PX

    def is_on_call_video_page(self) -> bool:
        url = self._driver.current_url.rstrip("/")
        return url.endswith("/call") or url.endswith("/vi/call")

    def is_on_call_chat_page(self) -> bool:
        return "/call/chat" in self._driver.current_url

    def _is_desktop_chat_sheet_open(self) -> bool:
        return self.is_element_visible(CHAT_SIDEBAR_SHEET) and self.is_element_visible(
            CHAT_SIDEBAR
        )

    def _is_mobile_chat_page_open(self) -> bool:
        if not self.is_on_call_chat_page():
            return False
        return self.is_element_visible(CHAT_FULL_PAGE) or self.is_element_visible(
            CHAT_FULL_PAGE_CLIENT
        )

    def is_chat_open(self) -> bool:
        if self.is_mobile_viewport():
            return self._is_mobile_chat_page_open()
        return self._is_desktop_chat_sheet_open()

    def _is_in_active_call(self) -> bool:
        if self.get_connection_status() == "in_call":
            return True
        if self.is_mobile_viewport() and self._is_mobile_chat_page_open():
            return True
        return False

    def ensure_on_call_video_page(self) -> None:
        if self.is_on_call_video_page():
            return
        if self._base_url:
            self._driver.get(f"{self._base_url}{self.PATH}")
        self.ensure_in_call()

    def is_post_call_idle_status(self) -> bool:
        return self.get_connection_status() in ("idle", "ended")

    def wait_post_call_idle(self, timeout: float | None = None) -> None:
        deadline = timeout or DEFAULT_TIMEOUT_SEC

        def _matches(_driver: WebDriver) -> bool:
            return self.is_post_call_idle_status()

        WebDriverWait(self._driver, deadline).until(_matches)

    def wait_connection_status(
        self,
        status: str,
        timeout: float | None = None,
    ) -> None:
        deadline = timeout or DEFAULT_TIMEOUT_SEC

        def _matches(_driver: WebDriver) -> bool:
            return self.get_connection_status() == status

        WebDriverWait(self._driver, deadline).until(_matches)

    def cancel_search(self) -> None:
        deadline = time.monotonic() + _CALL_READY_TIMEOUT_SEC
        while time.monotonic() < deadline:
            for selector in (CHAT_CANCEL_SEARCH_BUTTON, CHAT_END_CALL_BUTTON):
                for element in self._driver.find_elements(By.CSS_SELECTOR, selector):
                    if element.is_displayed():
                        _click(self._driver, element)
                        self.wait_post_call_idle(timeout=_CALL_READY_TIMEOUT_SEC)
                        self.wait_until_ready()
                        return
            time.sleep(0.2)
        raise TimeoutException("No visible cancel/end control while searching")

    def end_call(self) -> None:
        button = WebDriverWait(self._driver, DEFAULT_TIMEOUT_SEC).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, CHAT_END_CALL_BUTTON))
        )
        _click(self._driver, button)
        self.wait_post_call_idle(timeout=_CALL_READY_TIMEOUT_SEC)
        self.wait_until_ready()

    def _is_nav_link_visible(self, selector: str) -> bool:
        for element in self._driver.find_elements(By.CSS_SELECTOR, selector):
            if element.is_displayed():
                return True
        return False

    def _ensure_sidebar_open(self) -> None:
        deadline = time.monotonic() + DEFAULT_TIMEOUT_SEC
        while time.monotonic() < deadline:
            if self._is_nav_link_visible(SIDEBAR_VIDEO_CHAT):
                return
            trigger = self._driver.find_element(By.CSS_SELECTOR, SIDEBAR_TRIGGER)
            _native_click(self._driver, trigger)
        wait_visible(self._driver, (By.CSS_SELECTOR, SIDEBAR_VIDEO_CHAT))

    def _is_sidebar_collapsed(self) -> bool:
        for element in self._driver.find_elements(
            By.CSS_SELECTOR,
            '[data-slot="sidebar"][data-state="collapsed"]',
        ):
            if element.is_displayed():
                return True
        return False

    def _expand_sidebar_group(self, sub_nav_id: str) -> None:
        parent = sidebar_sub_parent(sub_nav_id)
        if not parent:
            return

        selector = sidebar_nav(sub_nav_id)
        if self._is_nav_link_visible(selector):
            return

        parent_trigger = self._driver.find_element(By.CSS_SELECTOR, sidebar_nav(parent))
        _native_click(self._driver, parent_trigger)
        if self._is_nav_link_visible(selector):
            return

        if self._is_sidebar_collapsed():
            sidebar_trigger = self._driver.find_element(By.CSS_SELECTOR, SIDEBAR_TRIGGER)
            _native_click(self._driver, sidebar_trigger)
            _native_click(self._driver, parent_trigger)
        wait_visible(self._driver, (By.CSS_SELECTOR, selector))

    def open_sidebar_nav(self, nav_id: str) -> None:
        self._ensure_sidebar_open()
        if sidebar_sub_parent(nav_id):
            self._expand_sidebar_group(nav_id)
        selector = sidebar_nav(nav_id)
        wait_visible(self._driver, (By.CSS_SELECTOR, selector), DEFAULT_TIMEOUT_SEC)
        link = WebDriverWait(self._driver, DEFAULT_TIMEOUT_SEC).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
        _click_nav_link(self._driver, link)
        expected_path = _NAV_URL_PARTS.get(nav_id)
        if expected_path:
            WebDriverWait(self._driver, DEFAULT_TIMEOUT_SEC).until(
                lambda driver: expected_path in driver.current_url
            )
        ready_selector = _NAV_READY_SELECTORS.get(nav_id)
        if ready_selector:
            wait_visible(
                self._driver,
                (By.CSS_SELECTOR, ready_selector),
                _CALL_READY_TIMEOUT_SEC,
            )

    def _visible_control(self, selector: str) -> WebElement:
        for element in self._driver.find_elements(By.CSS_SELECTOR, selector):
            if element.is_displayed():
                return element
        raise NoSuchElementException(f"No visible control for {selector!r}")

    def toggle_mute(self) -> None:
        button = self._visible_control(CHAT_MUTE_BUTTON)
        _click(self._driver, button)

    def is_mute_destructive(self) -> bool:
        button = self._visible_control(CHAT_MUTE_BUTTON)
        if button.get_attribute("data-variant") == "destructive":
            return True
        class_name = button.get_attribute("class") or ""
        return "bg-destructive" in class_name

    def toggle_video(self) -> None:
        button = self._visible_control(CHAT_VIDEO_TOGGLE_BUTTON)
        _click(self._driver, button)

    def is_camera_off_indicator_visible(self) -> bool:
        for element in self._driver.find_elements(
            By.CSS_SELECTOR,
            CHAT_CAMERA_OFF_INDICATOR,
        ):
            if element.is_displayed():
                return True
        return False

    def open_chat(self) -> None:
        if self.is_chat_open():
            return
        if self.is_mobile_viewport():
            self._open_chat_mobile()
            return
        self._open_chat_desktop()

    def _open_chat_desktop(self) -> None:
        overflow = WebDriverWait(self._driver, DEFAULT_TIMEOUT_SEC).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, CHAT_OVERFLOW_MENU_BUTTON))
        )
        _native_click(self._driver, overflow)
        toggle = WebDriverWait(self._driver, DEFAULT_TIMEOUT_SEC).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, CHAT_TOGGLE_BUTTON))
        )
        toggle.click()
        wait_visible(self._driver, (By.CSS_SELECTOR, CHAT_SIDEBAR_SHEET))
        wait_visible(self._driver, (By.CSS_SELECTOR, CHAT_SIDEBAR))

    def _open_chat_mobile(self) -> None:
        if self._is_mobile_chat_page_open():
            return
        self.ensure_on_call_video_page()
        overflow = WebDriverWait(self._driver, DEFAULT_TIMEOUT_SEC).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, CHAT_OVERFLOW_MENU_BUTTON))
        )
        _native_click(self._driver, overflow)
        toggle = WebDriverWait(self._driver, DEFAULT_TIMEOUT_SEC).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, CHAT_TOGGLE_BUTTON))
        )
        toggle.click()
        WebDriverWait(self._driver, DEFAULT_TIMEOUT_SEC).until(
            lambda _driver: "/call/chat" in _driver.current_url
        )
        wait_visible(self._driver, (By.CSS_SELECTOR, CHAT_FULL_PAGE))

    def ensure_chat_open(self) -> None:
        if self.is_chat_open():
            return
        self.open_chat()
        if not self.is_chat_open():
            self.open_chat()

    def ensure_in_call(self, timeout: float | None = None) -> None:
        deadline = time.monotonic() + (timeout or DEFAULT_TIMEOUT_SEC)

        def _matches(_driver: WebDriver) -> bool:
            return self._is_in_active_call()

        WebDriverWait(self._driver, deadline).until(_matches)

    def fill_chat_input(self, text: str) -> None:
        input_el = self._driver.find_element(By.CSS_SELECTOR, CHAT_INPUT)
        input_el.click()
        self._driver.execute_script(
            """
            const el = arguments[0];
            const value = arguments[1];
            const setter = Object.getOwnPropertyDescriptor(
              window.HTMLTextAreaElement.prototype,
              "value"
            )?.set;
            if (setter) {
              setter.call(el, value);
            } else {
              el.value = value;
            }
            el.dispatchEvent(new Event("input", { bubbles: true }));
            """,
            input_el,
            text,
        )
        time.sleep(_UI_SETTLE_SEC)
        if text.strip() and not self.is_send_enabled():
            input_el.clear()
            chunk_size = 50
            for start in range(0, len(text), chunk_size):
                input_el.send_keys(text[start : start + chunk_size])
            time.sleep(_UI_SETTLE_SEC)

    def is_send_enabled(self) -> bool:
        send = self._driver.find_element(By.CSS_SELECTOR, CHAT_SEND_BUTTON)
        disabled = send.get_attribute("disabled")
        aria_disabled = send.get_attribute("aria-disabled")
        return disabled is None and aria_disabled not in ("true", "True")

    def send_message(self, text: str) -> None:
        self.fill_chat_input(text)
        if text.strip():
            assert self.is_send_enabled(), (
                f"Send button disabled for non-empty message (len={len(text)})"
            )
        send = self._driver.find_element(By.CSS_SELECTOR, CHAT_SEND_BUTTON)
        _click(self._driver, send)

    def assert_message_not_visible(self, text: str, timeout: float = 3.0) -> None:
        if not text.strip():
            return
        self.ensure_chat_open()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                container = self._driver.find_element(
                    By.CSS_SELECTOR,
                    CHAT_MESSAGES_CONTAINER,
                )
                if text not in (container.text or ""):
                    return
            except NoSuchElementException:
                return
            time.sleep(0.25)
        raise AssertionError(f"Unexpected chat message visible: {text!r}")

    def wait_message_text(self, text: str, timeout: float | None = None) -> None:
        self.ensure_chat_open()
        chunks = call_chat_message_chunks(text)
        if not chunks:
            return
        total_timeout = timeout or DEFAULT_TIMEOUT_SEC
        per_chunk = max(total_timeout / len(chunks), DEFAULT_TIMEOUT_SEC)
        for chunk in chunks:
            self._wait_message_chunk(chunk, timeout=per_chunk)

    def _wait_message_chunk(self, text: str, timeout: float) -> None:
        def _contains(_driver: WebDriver) -> bool:
            try:
                container = _driver.find_element(
                    By.CSS_SELECTOR,
                    CHAT_MESSAGES_CONTAINER,
                )
            except NoSuchElementException:
                return False
            return text in (container.text or "")

        WebDriverWait(self._driver, timeout).until(_contains)

    def is_timer_visible(self) -> bool:
        for element in self._driver.find_elements(By.CSS_SELECTOR, CHAT_CALL_TIMER):
            if element.is_displayed():
                return True
        return False

    def is_local_video_visible(self) -> bool:
        for element in self._driver.find_elements(By.CSS_SELECTOR, CHAT_LOCAL_VIDEO):
            if element.is_displayed():
                return True
        return False

    def is_remote_video_visible(self) -> bool:
        for element in self._driver.find_elements(By.CSS_SELECTOR, CHAT_REMOTE_VIDEO):
            if element.is_displayed():
                return True
        return False

    def is_idle_container_visible(self) -> bool:
        for element in self._driver.find_elements(By.CSS_SELECTOR, CHAT_IDLE_CONTAINER):
            if element.is_displayed():
                return True
        return False

    def is_element_visible(self, selector: str) -> bool:
        for element in self._driver.find_elements(By.CSS_SELECTOR, selector):
            if element.is_displayed():
                return True
        return False

    def is_call_history_page_visible(self) -> bool:
        return self.is_element_visible(CALL_HISTORY_PAGE)

    def refresh_call_history(self) -> None:
        button = self._driver.find_element(By.CSS_SELECTOR, CALL_HISTORY_REFRESH_BUTTON)
        _click(self._driver, button)

    def ensure_idle(self) -> None:
        status = self.get_connection_status()
        if status in ("in_call", "searching", "matched", "reconnecting"):
            try:
                self.end_call()
            except Exception:
                try:
                    self.cancel_search()
                except Exception:
                    pass
        if self._base_url:
            self._driver.get(f"{self._base_url}{self.PATH}")
        self.wait_until_ready()

    def wait_in_call(self, timeout: float | None = None) -> None:
        self.wait_connection_status("in_call", timeout or _MATCH_TIMEOUT_SEC)
        wait_visible(
            self._driver,
            (By.CSS_SELECTOR, CHAT_CONTROLS_BAR),
            timeout or _MATCH_TIMEOUT_SEC,
        )

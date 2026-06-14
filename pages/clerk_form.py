"""Shared Clerk auth form steps (identifier, password, OTP, legal).

Các bước form xác thực Clerk dùng chung (identifier, password, OTP, legal).
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from helpers.locators import by_role, first_visible_css
from helpers.waits import (
    DEFAULT_TIMEOUT_SEC,
    wait_for_clerk_ready,
    wait_hidden,
    wait_until_element_displayed,
    wait_visible,
)
from pages.selectors.clerk import (
    _EMAIL_FIELDS,
    _EMAIL_INPUT_SCOPED_CSS,
    _LEGAL_FIELDS,
    _LEGAL_INPUT_SCOPED_CSS,
    _OTP_INPUT_LOCATOR,
    _PASSWORD_FIELDS,
    _PASSWORD_INPUT_SCOPED_CSS,
)
_CONTINUE = re.compile(r"continue", re.I)
_FORGOT_PASSWORD = re.compile(r"forgot password", re.I)

_SET_INPUT_VALUE_JS = """
const element = arguments[0];
const value = arguments[1];
const prototype = Object.getPrototypeOf(element);
const descriptor = Object.getOwnPropertyDescriptor(prototype, 'value');
const setter = descriptor && descriptor.set;
if (setter) {
    setter.call(element, value);
} else {
    element.value = value;
}
element.dispatchEvent(new Event('input', { bubbles: true }));
element.dispatchEvent(new Event('change', { bubbles: true }));
"""

_CLEAR_INPUT_VALUE_JS = """
const element = arguments[0];
const prototype = Object.getPrototypeOf(element);
const descriptor = Object.getOwnPropertyDescriptor(prototype, 'value');
const setter = descriptor && descriptor.set;
if (setter) {
    setter.call(element, '');
} else {
    element.value = '';
}
element.dispatchEvent(new Event('input', { bubbles: true }));
element.dispatchEvent(new Event('change', { bubbles: true }));
"""

_UI_SETTLE_SEC = 0.4


def clear_input_value(driver: WebDriver, inp: WebElement) -> None:
    """Clear a React-controlled input before filling a new value.

    Xóa input điều khiển bởi React trước khi điền giá trị mới.
    """
    driver.execute_script("arguments[0].focus(); arguments[0].select();", inp)
    try:
        inp.clear()
    except Exception:
        pass
    driver.execute_script(_CLEAR_INPUT_VALUE_JS, inp)
    time.sleep(_UI_SETTLE_SEC)


def password_needs_js_fill(password: str) -> bool:
    """Use the React-compatible setter when ChromeDriver cannot type the password.

    Dùng setter tương thích React khi ChromeDriver không gõ được mật khẩu.
    """
    return any(ord(ch) > 0xFFFF for ch in password)


def fill_password_input(
    driver: WebDriver,
    inp: WebElement,
    password: str,
) -> None:
    clear_input_value(driver, inp)
    if password_needs_js_fill(password):
        driver.execute_script(_SET_INPUT_VALUE_JS, inp, password)
    else:
        inp.send_keys(password)
    time.sleep(_UI_SETTLE_SEC)


def _clerk_input(
    driver: WebDriver,
    scoped_css: str,
    fields: str,
    *,
    role: str,
    name: str | re.Pattern[str],
) -> WebElement:
    el = first_visible_css(driver, scoped_css, fields)
    if el is not None:
        return el
    return by_role(driver, role, name=name)


class ClerkFormPage:
    """Base page object for Clerk forms with shared assertions and actions.

    Page object cơ sở cho form Clerk với assertion và thao tác dùng chung.
    """

    def __init__(self, driver: WebDriver) -> None:
        self._driver = driver

    def continue_button(self) -> WebElement:
        return by_role(self._driver, "button", name=_CONTINUE)

    def submit_with_continue(self, fill: Callable[[], None] | None = None) -> None:
        if fill is not None:
            fill()
        self.continue_button().click()


class IdentifierStep(ClerkFormPage):
    def email_input(self) -> WebElement:
        return _clerk_input(
            self._driver,
            _EMAIL_INPUT_SCOPED_CSS,
            _EMAIL_FIELDS,
            role="textbox",
            name=re.compile(r"identifier|emailAddress|email address", re.I),
        )

    def clear_email(self) -> None:
        clear_input_value(self._driver, self.email_input())

    def fill_email(self, email: str) -> None:
        inp = self.email_input()
        clear_input_value(self._driver, inp)
        if " " in email:
            self._driver.execute_script(_SET_INPUT_VALUE_JS, inp, email)
            return
        inp.send_keys(email)

    def wait_until_visible(self, timeout: float | None = None) -> None:
        wait_visible(self._driver, ("css selector", _EMAIL_INPUT_SCOPED_CSS), timeout)

    def wait_until_hidden(self, timeout: float | None = None) -> None:
        wait_hidden(self._driver, ("css selector", _EMAIL_INPUT_SCOPED_CSS), timeout)

    @classmethod
    def open(
        cls,
        driver: WebDriver,
        base_url: str,
        *,
        path: str,
        timeout: float | None = None,
    ) -> IdentifierStep:
        driver.get(f"{base_url.rstrip('/')}{path}")
        wait_for_clerk_ready(driver)
        page = cls(driver)
        page.wait_until_visible(timeout)
        return page


class PasswordStep(ClerkFormPage):
    def forgot_password_link(self) -> WebElement:
        return by_role(self._driver, "link", name=_FORGOT_PASSWORD)

    def click_forgot_password(self) -> None:
        self.forgot_password_link().click()

    def password_input(self) -> WebElement:
        return _clerk_input(
            self._driver,
            _PASSWORD_INPUT_SCOPED_CSS,
            _PASSWORD_FIELDS,
            role="textbox",
            name=re.compile(r"password", re.I),
        )

    def clear_password(self) -> None:
        clear_input_value(self._driver, self.password_input())

    def fill_password(self, password: str) -> None:
        fill_password_input(self._driver, self.password_input(), password)

    def wait_until_visible(self, timeout: float | None = None) -> None:
        wait_visible(self._driver, ("css selector", _PASSWORD_INPUT_SCOPED_CSS), timeout)

    def wait_until_hidden(self, timeout: float | None = None) -> None:
        wait_hidden(self._driver, ("css selector", _PASSWORD_INPUT_SCOPED_CSS), timeout)


class LegalStep(ClerkFormPage):
    def legal_input(self) -> WebElement:
        return _clerk_input(
            self._driver,
            _LEGAL_INPUT_SCOPED_CSS,
            _LEGAL_FIELDS,
            role="checkbox",
            name=re.compile(r"legalAccepted", re.I),
        )

    def clear_legal(self) -> None:
        inp = self.legal_input()
        if inp.is_selected():
            inp.click()

    def accept_legal(self) -> None:
        inp = self.legal_input()
        if not inp.is_selected():
            inp.click()

    def wait_until_visible(self, timeout: float | None = None) -> None:
        wait_visible(self._driver, ("css selector", _LEGAL_INPUT_SCOPED_CSS), timeout)

    def wait_until_hidden(self, timeout: float | None = None) -> None:
        wait_hidden(self._driver, ("css selector", _LEGAL_INPUT_SCOPED_CSS), timeout)


class OTPStep(ClerkFormPage):
    _OTP_NAME = re.compile(r"verification code|one-time|enter code", re.I)

    def otp_input(self) -> WebElement:
        try:
            el = self._driver.find_element(*_OTP_INPUT_LOCATOR)
            if el.is_displayed():
                return el
        except Exception:
            pass
        return by_role(self._driver, "textbox", name=_OTP_NAME)

    def clear_otp(self) -> None:
        clear_input_value(self._driver, self.otp_input())

    def fill_otp(self, otp: str, *, delay: float = 0.1) -> None:
        inp = self.otp_input()
        clear_input_value(self._driver, inp)
        for char in otp:
            inp.send_keys(char)
            time.sleep(delay)

    def wait_until_visible(self, timeout: float | None = None) -> None:
        wait_until_element_displayed(self._driver, self.otp_input, timeout)

    def wait_until_hidden(self, timeout: float | None = None) -> None:
        wait_hidden(self._driver, _OTP_INPUT_LOCATOR, timeout)

"""Shared Clerk auth form steps (identifier, password, OTP, legal)."""

from __future__ import annotations

import re
import time

from collections.abc import Callable

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from helpers.locators import (
    assert_text_on_screen,
    by_role,
    first_visible_css,
    scoped_css,
)
from helpers.validation import InputRef, assert_input_and_screen_message
from helpers.waits import DEFAULT_TIMEOUT_SEC, wait_for_clerk_ready, wait_hidden, wait_visible

_CLERK_SCOPE = '[data-clerk-ready="true"] '
_EMAIL_FIELDS = (
    'input[name="identifier"], input#identifier, '
    'input[name="emailAddress"], input#emailAddress, '
    'input[type="email"]'
)
_PASSWORD_FIELDS = 'input[name="password"], input#password, input[type="password"]'
_LEGAL_FIELDS = 'input[name="legalAccepted"], input#legalAccepted-field'
_OTP_INPUT_CSS = (
    'input[autocomplete="one-time-code"], input[name*="code"], '
    'input[name*="otp"], input[inputmode="numeric"]'
)
_EMAIL_INPUT_SCOPED_CSS = scoped_css(_CLERK_SCOPE, _EMAIL_FIELDS)
_PASSWORD_INPUT_SCOPED_CSS = scoped_css(_CLERK_SCOPE, _PASSWORD_FIELDS)
_LEGAL_INPUT_SCOPED_CSS = scoped_css(_CLERK_SCOPE, _LEGAL_FIELDS)
_OTP_INPUT_LOCATOR = ("css selector", _OTP_INPUT_CSS)
_CONTINUE = re.compile(r"continue", re.I)
_FORGOT_PASSWORD = re.compile(r"forgot password", re.I)

_SET_INPUT_VALUE_JS = """
arguments[0].value = arguments[1];
arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
"""


def _email_local_part(email: str) -> str:
    return email.split("@", 1)[0]


class ClerkFormPage:
    """Base page object for Clerk forms with shared assertions and actions."""

    def __init__(self, driver: WebDriver) -> None:
        self._driver = driver

    def continue_button(self) -> WebElement:
        return by_role(self._driver, "button", name=_CONTINUE)

    def assert_screen_contains(
        self,
        text: str,
        *,
        exact: bool = False,
        timeout: float = 10,
    ) -> WebElement:
        """Assert that ``text`` is visible anywhere on screen."""
        return assert_text_on_screen(
            self._driver,
            text,
            exact=exact,
            timeout=timeout,
        )

    def assert_error_message(
        self,
        text: str,
        *,
        exact: bool = False,
        timeout: float = 10,
    ) -> WebElement:
        """Assert the screen shows an error containing ``text``."""
        return self.assert_screen_contains(text, exact=exact, timeout=timeout)

    def assert_input_and_screen_message(
        self,
        input_el: InputRef,
        text: str,
        *,
        exact: bool = False,
        timeout: float = 10,
    ) -> None:
        """Assert HTML5 ``validationMessage`` and/or visible screen contain ``text``."""
        assert_input_and_screen_message(
            self._driver,
            input_el,
            text,
            exact=exact,
            timeout=timeout,
        )


class IdentifierStep(ClerkFormPage):
    def email_input(self) -> WebElement:
        el = first_visible_css(self._driver, _EMAIL_INPUT_SCOPED_CSS, _EMAIL_FIELDS)
        if el is not None:
            return el
        return by_role(
            self._driver,
            "textbox",
            name=re.compile(r"identifier|emailAddress|email address", re.I),
        )

    def fill_email(self, email: str) -> None:
        inp = self.email_input()
        inp.clear()
        if " " in _email_local_part(email):
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
        el = first_visible_css(self._driver, _PASSWORD_INPUT_SCOPED_CSS, _PASSWORD_FIELDS)
        if el is not None:
            return el
        return by_role(self._driver, "textbox", name=re.compile(r"password", re.I))

    def fill_password(self, password: str) -> None:
        inp = self.password_input()
        inp.clear()
        inp.send_keys(password)

    def wait_until_visible(self, timeout: float | None = None) -> None:
        wait_visible(self._driver, ("css selector", _PASSWORD_INPUT_SCOPED_CSS), timeout)

    def wait_until_hidden(self, timeout: float | None = None) -> None:
        wait_hidden(self._driver, ("css selector", _PASSWORD_INPUT_SCOPED_CSS), timeout)


class LegalStep(ClerkFormPage):
    def legal_input(self) -> WebElement:
        el = first_visible_css(self._driver, _LEGAL_INPUT_SCOPED_CSS, _LEGAL_FIELDS)
        if el is not None:
            return el
        return by_role(self._driver, "checkbox", name=re.compile(r"legalAccepted", re.I))

    def accept_legal(self) -> None:
        self.legal_input().click()

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

    def fill_otp(self, otp: str, *, delay: float = 0.1) -> None:
        inp = self.otp_input()
        inp.clear()
        for char in otp:
            inp.send_keys(char)
            time.sleep(delay)

    def wait_until_visible(self, timeout: float | None = None) -> None:
        t = timeout or DEFAULT_TIMEOUT_SEC

        def _ready(_driver: WebDriver) -> bool:
            try:
                return self.otp_input().is_displayed()
            except Exception:
                return False

        WebDriverWait(self._driver, t).until(_ready)

    def wait_until_hidden(self, timeout: float | None = None) -> None:
        wait_hidden(self._driver, _OTP_INPUT_LOCATOR, timeout)

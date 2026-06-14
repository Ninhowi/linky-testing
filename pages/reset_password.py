"""Reset-password form after sign-in identifier → forgot → OTP.

Form đặt lại mật khẩu sau đăng nhập identifier → quên mật khẩu → OTP.
"""

from __future__ import annotations

import re
import time

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from helpers.locators import by_role, first_visible_css
from helpers.waits import DEFAULT_TIMEOUT_SEC, wait_hidden, wait_until_element_displayed
from pages.clerk_form import (
    ClerkFormPage,
    _UI_SETTLE_SEC,
    _clerk_input,
    fill_password_input,
)
from pages.selectors.clerk import (
    _CONFIRM_PASSWORD_FIELDS,
    _CONFIRM_PASSWORD_SCOPED,
    _NEW_PASSWORD_FIELDS,
    _NEW_PASSWORD_SCOPED,
    _SIGN_OUT_FIELDS,
    _SIGN_OUT_SCOPED,
    _SUBMIT_BUTTON_CSS,
)
from pages.sign_in import SignInPage

_SUBMIT_RESET = re.compile(r"reset password", re.I)


class ResetPasswordFormStep(ClerkFormPage):
    """Set-new-password form after OTP verification.

    Form đặt mật khẩu mới sau khi xác minh OTP.
    """

    def new_password_input(self) -> WebElement:
        return _clerk_input(
            self._driver,
            _NEW_PASSWORD_SCOPED,
            _NEW_PASSWORD_FIELDS,
            role="textbox",
            name=re.compile(r"new password", re.I),
        )

    def confirm_password_input(self) -> WebElement:
        return _clerk_input(
            self._driver,
            _CONFIRM_PASSWORD_SCOPED,
            _CONFIRM_PASSWORD_FIELDS,
            role="textbox",
            name=re.compile(r"confirm password", re.I),
        )

    def sign_out_checkbox(self) -> WebElement:
        return _clerk_input(
            self._driver,
            _SIGN_OUT_SCOPED,
            _SIGN_OUT_FIELDS,
            role="checkbox",
            name=re.compile(r"sign out of all other devices", re.I),
        )

    def _fill_input(self, inp: WebElement, value: str) -> None:
        fill_password_input(self._driver, inp, value)

    def fill_new_password(self, password: str) -> None:
        self._fill_input(self.new_password_input(), password)

    def fill_confirm_password(self, password: str) -> None:
        self._fill_input(self.confirm_password_input(), password)

    def fill_passwords(
        self,
        new_password: str | None,
        confirm_password: str | None,
    ) -> None:
        """Fill both fields, then pause for Clerk validation UI to update.

        Điền cả hai trường, rồi tạm dừng để UI xác thực Clerk cập nhật.
        """
        if new_password:
            self.fill_new_password(new_password)
        if confirm_password:
            self.fill_confirm_password(confirm_password)
        if new_password or confirm_password:
            time.sleep(_UI_SETTLE_SEC)

    def set_sign_out_all_devices(self, enabled: bool) -> None:
        cb = self.sign_out_checkbox()
        if cb.is_selected() != enabled:
            cb.click()

    def reset_password_button(self) -> WebElement:
        el = first_visible_css(self._driver, _SUBMIT_BUTTON_CSS)
        if el is not None:
            return el
        return by_role(self._driver, "button", name=_SUBMIT_RESET)

    def submit(self) -> None:
        btn = self.reset_password_button()
        self._driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", btn
        )

        def _enabled(_driver: WebDriver) -> bool:
            try:
                return self.reset_password_button().is_enabled()
            except Exception:
                return False

        WebDriverWait(self._driver, DEFAULT_TIMEOUT_SEC).until(_enabled)
        self._driver.execute_script("arguments[0].click();", self.reset_password_button())

    def wait_until_visible(self, timeout: float | None = None) -> None:
        wait_until_element_displayed(self._driver, self.new_password_input, timeout)

    def wait_until_hidden(self, timeout: float | None = None) -> None:
        wait_hidden(self._driver, ("css selector", _NEW_PASSWORD_SCOPED), timeout)


class ResetPasswordPage(SignInPage):
    """Sign-in path through OTP, plus the set-new-password form.

    Luồng đăng nhập qua OTP, kèm form đặt mật khẩu mới.
    """

    def __init__(self, driver: WebDriver) -> None:
        super().__init__(driver)
        self.reset = ResetPasswordFormStep(driver)

    @classmethod
    def open(
        cls,
        driver: WebDriver,
        base_url: str,
        *,
        path: str = "/sign-in",
        timeout: float | None = None,
    ) -> ResetPasswordPage:
        SignInPage.open(driver, base_url, path=path, timeout=timeout)
        return cls(driver)

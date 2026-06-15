"""Sign-in page objects (Clerk identifier, password, and OTP steps).

Page object đăng nhập (các bước identifier, password và OTP của Clerk).
"""

from __future__ import annotations

import re

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from helpers.browser.locators import by_role
from pages.clerk_form import ClerkFormPage, IdentifierStep, OTPStep, PasswordStep

_SIGN_IN_PATH = "/sign-in"
_RESET_PASSWORD = re.compile(r"reset your password", re.I)


class IdentifierPage(IdentifierStep):
    def submit_email(self, email: str) -> None:
        self.submit_with_continue(lambda: self.fill_email(email))

    def submit_empty(self) -> None:
        self.submit_with_continue()

    @classmethod
    def open(
        cls,
        driver: WebDriver,
        base_url: str,
        *,
        path: str = _SIGN_IN_PATH,
        timeout: float | None = None,
    ) -> IdentifierPage:
        return super().open(driver, base_url, path=path, timeout=timeout)


class PasswordPage(PasswordStep):
    def submit_password(self, password: str) -> None:
        self.submit_with_continue(lambda: self.fill_password(password))

    def submit_empty(self) -> None:
        self.submit_with_continue()


class ForgotPasswordPage(ClerkFormPage):
    """Forgot-password chooser reached from the password step.

    Màn hình chọn quên mật khẩu, truy cập từ bước password.
    """

    def reset_your_password_button(self) -> WebElement:
        return by_role(self._driver, "button", name=_RESET_PASSWORD)

    def click_reset_your_password(self) -> None:
        self.reset_your_password_button().click()


class SignInPage(ClerkFormPage):
    """Convenience facade for the multi-step sign-in flow.

    Facade tiện lợi cho luồng đăng nhập nhiều bước.
    """

    def __init__(self, driver: WebDriver) -> None:
        super().__init__(driver)
        self.identifier = IdentifierPage(driver)
        self.password = PasswordPage(driver)
        self.forgot = ForgotPasswordPage(driver)
        self.otp = OTPStep(driver)

    @classmethod
    def open(
        cls,
        driver: WebDriver,
        base_url: str,
        *,
        path: str = _SIGN_IN_PATH,
        timeout: float | None = None,
    ) -> SignInPage:
        IdentifierPage.open(driver, base_url, path=path, timeout=timeout)
        return cls(driver)

    def submit_credentials(self, email: str, password: str) -> None:
        self.identifier.submit_email(email)
        self.password.wait_until_visible()
        self.password.submit_password(password)

    def advance_to_otp(self, email: str, password: str) -> None:
        """Submit valid credentials and wait for the OTP / factor-two step.

        Gửi thông tin đăng nhập hợp lệ và chờ bước OTP / factor-two.
        """
        self.submit_credentials(email, password)
        self.otp.wait_until_visible()

    def submit_credentials_and_otp(self, email: str, password: str, otp: str) -> None:
        self.advance_to_otp(email, password)
        self.otp.fill_otp(otp)

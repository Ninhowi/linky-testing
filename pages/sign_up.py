"""Sign-up page objects (single registration form, then OTP).

Page object đăng ký (một form đăng ký, rồi OTP).
"""

from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from helpers.waits import wait_for_clerk_ready
from pages.clerk_form import ClerkFormPage, IdentifierStep, LegalStep, OTPStep, PasswordStep

_SIGN_UP_PATH = "/sign-up"


class SignUpFormStep(ClerkFormPage):
    """Registration form with email, password, and legal fields visible together.

    Form đăng ký với email, password và trường điều khoản hiển thị cùng lúc.
    """

    def __init__(self, driver: WebDriver) -> None:
        super().__init__(driver)
        self._email = IdentifierStep(driver)
        self._password = PasswordStep(driver)
        self._legal = LegalStep(driver)

    def email_input(self) -> WebElement:
        return self._email.email_input()

    def password_input(self) -> WebElement:
        return self._password.password_input()

    def legal_input(self) -> WebElement:
        return self._legal.legal_input()

    def fill_email(self, email: str) -> None:
        self._email.fill_email(email)

    def fill_password(self, password: str) -> None:
        self._password.fill_password(password)

    def accept_legal(self) -> None:
        self._legal.accept_legal()

    def clear_fields(self) -> None:
        """Reset email, password, and legal checkbox before filling the next case.

        Xóa email, password và bỏ chọn checkbox điều khoản trước case tiếp theo.
        """
        self._email.clear_email()
        self._password.clear_password()
        self._legal.clear_legal()

    def fill(
        self,
        email: str | None = None,
        password: str | None = None,
        *,
        accept_legal: bool = False,
    ) -> None:
        """Fill any subset of the visible registration fields.

        Điền bất kỳ tập con nào của các trường đăng ký hiển thị.
        """
        self.clear_fields()
        if email:
            self.fill_email(email)
        if password:
            self.fill_password(password)
        if accept_legal:
            self.accept_legal()

    def submit(self) -> None:
        self.continue_button().click()

    def submit_empty(self) -> None:
        self.submit()

    def wait_until_visible(self, timeout: float | None = None) -> None:
        self._email.wait_until_visible(timeout)
        self._password.wait_until_visible(timeout)
        self._legal.wait_until_visible(timeout)

    def wait_until_hidden(self, timeout: float | None = None) -> None:
        self._email.wait_until_hidden(timeout)

    @classmethod
    def open(
        cls,
        driver: WebDriver,
        base_url: str,
        *,
        path: str = _SIGN_UP_PATH,
        timeout: float | None = None,
    ) -> SignUpFormStep:
        driver.get(f"{base_url.rstrip('/')}{path}")
        wait_for_clerk_ready(driver)
        page = cls(driver)
        page.wait_until_visible(timeout)
        return page


class SignUpPage(ClerkFormPage):
    """Sign-up flow: one registration form, then OTP verification.

    Luồng đăng ký: một form đăng ký, rồi xác minh OTP.
    """

    def __init__(self, driver: WebDriver) -> None:
        super().__init__(driver)
        self.form = SignUpFormStep(driver)
        self.otp = OTPStep(driver)

    @classmethod
    def open(
        cls,
        driver: WebDriver,
        base_url: str,
        *,
        path: str = _SIGN_UP_PATH,
        timeout: float | None = None,
    ) -> SignUpPage:
        SignUpFormStep.open(driver, base_url, path=path, timeout=timeout)
        return cls(driver)

    def submit_registration(
        self,
        email: str,
        password: str,
        *,
        accept_legal: bool = True,
    ) -> None:
        self.form.fill(email, password, accept_legal=accept_legal)
        self.form.submit()

    def advance_to_otp(self, email: str, password: str) -> None:
        self.submit_registration(email, password)
        self.otp.wait_until_visible()

    def submit_registration_and_otp(self, email: str, password: str, otp: str) -> None:
        self.advance_to_otp(email, password)
        self.otp.fill_otp(otp)

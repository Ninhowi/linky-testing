"""OTP / verify-email-address and factor-two pages."""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage


class VerifyEmailPage(BasePage):
    """OTP input (sign-up verify-email-address or login factor-two)."""

    OTP_INPUT = (By.XPATH, "//input[@autocomplete='one-time-code']")
    OTP_INPUT_CSS = (By.CSS_SELECTOR, "input[autocomplete='one-time-code']")
    ERROR_UNDEFINED = (By.ID, "error-undefined")

    def wait_for_otp_field_signup(self) -> None:
        """Sign-up flow uses XPath."""
        self.wait.until(EC.presence_of_element_located(self.OTP_INPUT))

    def wait_for_otp_field_login(self) -> None:
        """Login flow uses CSS."""
        self.wait.until(EC.presence_of_element_located(self.OTP_INPUT_CSS))

    def enter_otp(self, otp: str, for_login: bool = False) -> None:
        locator = self.OTP_INPUT_CSS if for_login else self.OTP_INPUT
        el = self.wait.until(EC.presence_of_element_located(locator))
        el.send_keys(otp or "")

    def get_otp_error_text(self) -> str:
        els = self.driver.find_elements(*self.ERROR_UNDEFINED)
        return els[0].text.strip() if els else ""

    def is_still_on_verify_signup(self) -> bool:
        return "verify-email-address" in self.current_url

    def is_still_on_factor_two(self) -> bool:
        return "factor-two" in self.current_url

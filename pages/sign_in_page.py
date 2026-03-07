"""Sign-in page: email step, password step, and error elements."""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from pages.base_page import BasePage


class SignInPage(BasePage):
    """Page object for /sign-in."""

    EMAIL_FIELD = (By.NAME, "identifier")
    PASSWORD_FIELD = (By.NAME, "password")
    ERROR_IDENTIFIER = (By.ID, "error-identifier")
    ERROR_PASSWORD = (By.ID, "error-password")

    def open_sign_in(self) -> None:
        self.open("/sign-in")

    def fill_email_and_submit(self, email: str) -> None:
        el = self.wait.until(EC.presence_of_element_located(self.EMAIL_FIELD))
        el.send_keys(str(email or ""))
        el.send_keys(Keys.RETURN)

    def get_email_element(self):
        return self.driver.find_element(*self.EMAIL_FIELD)

    def fill_password_and_submit(self, password: str) -> None:
        el = self.wait.until(EC.presence_of_element_located(self.PASSWORD_FIELD))
        el.send_keys(password or "")
        el.send_keys(Keys.RETURN)

    def get_identifier_error_text(self) -> str:
        els = self.driver.find_elements(*self.ERROR_IDENTIFIER)
        return els[0].text.strip() if els else ""

    def get_password_error_text(self) -> str:
        els = self.driver.find_elements(*self.ERROR_PASSWORD)
        return els[0].text.strip() if els else ""

    def is_on_factor_two(self) -> bool:
        return "factor-two" in self.current_url

    def is_on_success(self) -> bool:
        return "linkynow.site" in self.current_url and "sign-in" not in self.current_url

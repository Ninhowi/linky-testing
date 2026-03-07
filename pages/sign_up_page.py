"""Sign-up page: form fields, validation, submit, and error elements."""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from pages.base_page import BasePage
from utils.safe_input import safe_input
from utils.generate_email import generate_email


class SignUpPage(BasePage):
    """Page object for /sign-up."""

    # Locators
    FIRST_NAME = (By.NAME, "firstName")
    LAST_NAME = (By.NAME, "lastName")
    EMAIL = (By.NAME, "emailAddress")
    PASSWORD = (By.NAME, "password")
    LEGAL_ACCEPTED = (By.NAME, "legalAccepted")
    ERROR_PASSWORD = (By.ID, "error-password")
    ERROR_FIRST_NAME = (By.ID, "error-firstName")
    ERROR_LAST_NAME = (By.ID, "error-lastName")
    ERROR_EMAIL = (By.ID, "error-emailAddress")
    ALERT_TEXT = (By.CLASS_NAME, "cl-alertText")
    ERROR_ANY = (By.CSS_SELECTOR, "[id^='error-']")

    def open_sign_up(self) -> None:
        self.open("/sign-up")

    def fill_first_name(self, value: str) -> None:
        el = self.wait.until(EC.presence_of_element_located(self.FIRST_NAME))
        safe_input(self.driver, el, value or "")

    def fill_last_name(self, value: str) -> None:
        el = self.wait.until(EC.presence_of_element_located(self.LAST_NAME))
        safe_input(self.driver, el, value or "")

    def fill_email(
        self,
        value: str,
        enable_generate: bool = True,
        auto_remove_content: str | None = None,
        auto_remove_content_position: str | None = None,
    ) -> str:
        el = self.wait.until(EC.presence_of_element_located(self.EMAIL))
        final = generate_email(
            base_email=value or "",
            enable_generate_email=enable_generate,
            auto_remove_content=auto_remove_content,
            auto_remove_content_position=auto_remove_content_position,
        )
        el.send_keys(final)
        return final

    def fill_password(self, value: str) -> None:
        el = self.wait.until(EC.presence_of_element_located(self.PASSWORD))
        el.send_keys(value or "")

    def accept_legal(self) -> None:
        el = self.wait.until(EC.presence_of_element_located(self.LEGAL_ACCEPTED))
        el.click()

    def submit_form(self) -> None:
        el = self.wait.until(EC.presence_of_element_located(self.PASSWORD))
        el.send_keys(Keys.RETURN)

    def get_email_element(self):
        return self.driver.find_element(*self.EMAIL)

    def get_password_element(self):
        return self.driver.find_element(*self.PASSWORD)

    def get_password_error_text(self) -> str:
        els = self.driver.find_elements(*self.ERROR_PASSWORD)
        return els[0].text.strip() if els else ""

    def get_alert_text(self) -> str:
        els = self.driver.find_elements(*self.ALERT_TEXT)
        return els[0].text.strip() if els else ""

    def get_inline_errors_text(self) -> str:
        els = self.driver.find_elements(*self.ERROR_ANY)
        return " ".join(e.text.strip() for e in els if e.text.strip())

    def is_on_verify_email(self) -> bool:
        return "verify-email-address" in self.current_url

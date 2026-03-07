"""Post-login/signup dashboard (success state)."""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage


class DashboardPage(BasePage):
    """Success page with start-chat button."""

    START_CHAT_BUTTON = (By.CSS_SELECTOR, "[data-testid='start-chat-button']")
    OTP_SUCCESS_TEXT = (By.CLASS_NAME, "cl-otpCodeFieldSuccessText")

    def wait_for_start_chat(self) -> None:
        self.wait_auth.until(
            EC.presence_of_element_located(self.START_CHAT_BUTTON)
        )

    def wait_for_otp_success_or_chat_login(self) -> None:
        """Login OTP success or chat button."""
        self.wait_auth.until(
            EC.any_of(
                EC.presence_of_element_located(self.OTP_SUCCESS_TEXT),
                EC.presence_of_element_located(self.START_CHAT_BUTTON),
            )
        )

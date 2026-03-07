"""Login flow using page objects."""
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from pages.sign_in_page import SignInPage
from pages.verify_email_page import VerifyEmailPage
from pages.dashboard_page import DashboardPage


def run_login_flow(
    sign_in_page: SignInPage,
    verify_page: VerifyEmailPage,
    dashboard_page: DashboardPage,
    email: str,
    password: str,
    otp: str,
    message: str | None,
) -> None:
    email = email or ""
    password = password or ""
    otp = otp or ""

    print("[STEP] Email step")
    sign_in_page.fill_email_and_submit(email)

    is_valid = sign_in_page.driver.execute_script(
        "return arguments[0].checkValidity();",
        sign_in_page.get_email_element(),
    )
    print(f"[STATE] Browser email valid={is_valid}")

    if not is_valid:
        validation_message = sign_in_page.driver.execute_script(
            "return arguments[0].validationMessage;",
            sign_in_page.get_email_element(),
        )
        print(f"[VALIDATION MESSAGE - EMAIL]: {validation_message}")
        print(f"[ASSERT] Expect message contains: '{message}'")
        assert message in validation_message
        return

    print("[WAIT] Waiting for email validation result...")
    try:
        sign_in_page.wait.until(
            EC.any_of(
                EC.presence_of_element_located((By.ID, "error-identifier")),
                EC.presence_of_element_located((By.NAME, "password")),
            )
        )
    except TimeoutException:
        print("[WARN] Timeout waiting email result")

    identifier_error = sign_in_page.get_identifier_error_text()
    if identifier_error:
        print(f"[!] Email invalid - Error: {identifier_error}")
        print(f"[ASSERT] Expect message contains: '{message}'")
        assert message in identifier_error
        return

    print("[+] Email valid -> Go to password step")
    sign_in_page.fill_password_and_submit(password)

    print("[WAIT] Waiting for password validation result...")
    try:
        sign_in_page.wait.until(
            EC.any_of(
                EC.presence_of_element_located((By.ID, "error-password")),
                EC.url_contains("factor-two"),
                EC.url_contains("linkynow.site"),
            )
        )
    except TimeoutException:
        print("[WARN] Timeout waiting password result")

    password_error = sign_in_page.get_password_error_text()
    if password_error:
        print(f"[!] Password invalid - Error: {password_error}")
        print(f"[ASSERT] Expect message contains: '{message}'")
        assert message in password_error
        return

    print("[+] Password valid")

    if sign_in_page.is_on_factor_two():
        print("[FLOW] OTP required (new device)")
        verify_page.wait_for_otp_field_login()
        print(f"[+] Input OTP: '{otp}'")
        verify_page.enter_otp(otp, for_login=True)

        print("[WAIT] Waiting OTP result...")
        try:
            sign_in_page.wait_auth.until(
                EC.any_of(
                    EC.presence_of_element_located((By.CLASS_NAME, "cl-otpCodeFieldSuccessText")),
                    EC.presence_of_element_located((By.ID, "error-undefined")),
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[data-testid='start-chat-button']")
                    ),
                )
            )
        except TimeoutException:
            print("[WARN] Timeout waiting OTP result")

        if not verify_page.is_still_on_factor_two():
            print("[SUCCESS] Login successful after OTP")
            dashboard_page.wait_for_start_chat()
            return

        error_otp = verify_page.get_otp_error_text()
        if error_otp:
            print(f"[!] OTP invalid - Error: {error_otp}")
            print(f"[ASSERT] Expect message contains: '{message}'")
            assert message in error_otp
            return

    print("[SUCCESS] Login successful")
    dashboard_page.wait_for_start_chat()

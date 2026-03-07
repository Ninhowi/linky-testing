"""Sign-up flow using page objects. Replicates original validation, server wait, OTP, assertions."""
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from pages.sign_up_page import SignUpPage
from pages.verify_email_page import VerifyEmailPage
from pages.dashboard_page import DashboardPage


def run_signup_flow(
    sign_up_page: SignUpPage,
    verify_page: VerifyEmailPage,
    dashboard_page: DashboardPage,
    first_name: str,
    last_name: str,
    email: str,
    password: str,
    otp: str,
    message: str | None,
    auto_remove_content: str | None,
    auto_remove_content_position: str | None,
    enable_generate_email: bool = True,
) -> None:
    first_name = first_name or ""
    last_name = last_name or ""
    email = email or ""
    password = password or ""
    otp = otp or ""

    if message and (
        "email address already in use" in (message or "")
        or "email address is taken" in (message or "")
    ):
        print("[INFO] Duplicate email scenario → disable email auto-generate")
        enable_generate_email = False

    print("[STEP] Input basic fields")
    sign_up_page.fill_first_name(first_name)
    sign_up_page.fill_last_name(last_name)
    final_email = sign_up_page.fill_email(
        email,
        enable_generate=enable_generate_email,
        auto_remove_content=auto_remove_content,
        auto_remove_content_position=auto_remove_content_position,
    )
    print(f"[+] Input Email (final): '{final_email}'")
    sign_up_page.fill_password(password)

    # Password length validation branch
    if message and "72 characters" in message:
        print("[BRANCH] Password length validation case")
        error_text = sign_up_page.get_password_error_text()
        print(f"[ERROR TEXT] {error_text}")
        print(f"[ASSERT] Expect message contains: '{message}'")
        assert message in error_text
        return

    sign_up_page.accept_legal()
    print("[ACTION] Submit form (ENTER)")
    sign_up_page.submit_form()

    # Browser validation
    email_el = sign_up_page.get_email_element()
    password_el = sign_up_page.get_password_element()
    is_valid_email = sign_up_page.driver.execute_script(
        "return arguments[0].checkValidity();", email_el
    )
    is_valid_password = sign_up_page.driver.execute_script(
        "return arguments[0].checkValidity();", password_el
    )
    print(f"[STATE] is_valid_email={is_valid_email}, is_valid_password={is_valid_password}")

    if not is_valid_email:
        msg = sign_up_page.driver.execute_script(
            "return arguments[0].validationMessage;", email_el
        )
        print(f"[VALIDATION MESSAGE - EMAIL] {msg}")
        print(f"[ASSERT] Expect message contains: '{message}'")
        assert message in msg
        return

    if not is_valid_password:
        msg = sign_up_page.driver.execute_script(
            "return arguments[0].validationMessage;", password_el
        )
        print(f"[VALIDATION MESSAGE - PASSWORD] {msg}")
        print(f"[ASSERT] Expect message contains: '{message}'")
        assert message in msg
        return

    print("[WAIT] Waiting server response...")
    try:
        sign_up_page.wait.until(
            EC.any_of(
                EC.presence_of_element_located((By.ID, "error-firstName")),
                EC.presence_of_element_located((By.ID, "error-lastName")),
                EC.presence_of_element_located((By.ID, "error-emailAddress")),
                EC.presence_of_element_located((By.ID, "error-password")),
                EC.presence_of_element_located((By.CLASS_NAME, "cl-alertText")),
                EC.url_contains("verify-email-address"),
            )
        )
    except TimeoutException:
        print("[WARN] Timeout waiting server response")

    alert_text = sign_up_page.get_alert_text()
    if alert_text:
        print(f"[ALERT ERROR] {alert_text}")
        print(f"[ASSERT] Expect message contains: '{message}'")
        assert message in alert_text
        return

    errors_text = sign_up_page.get_inline_errors_text()
    if errors_text:
        print(f"[INLINE ERRORS] {errors_text}")
        print(f"[ASSERT] Expect message contains: '{message}'")
        assert message in errors_text
        return

    if sign_up_page.is_on_verify_email():
        print("[FLOW] OTP verification required")
        verify_page.wait_for_otp_field_signup()
        print(f"[+] Input OTP: '{otp}'")
        verify_page.enter_otp(otp, for_login=False)

        print("[WAIT] Waiting OTP result...")
        try:
            sign_up_page.wait_auth.until(
                EC.any_of(
                    EC.url_contains("linkynow.site"),
                    EC.presence_of_element_located((By.ID, "error-undefined")),
                    EC.presence_of_element_located(
                        (By.XPATH, "//a[@data-testid='start-chat-button']")
                    ),
                )
            )
        except TimeoutException:
            print("[WARN] Timeout waiting OTP result")

        if not verify_page.is_still_on_verify_signup():
            print("[SUCCESS] Sign up successful after OTP")
            dashboard_page.wait_for_start_chat()
            return

        error_otp = verify_page.get_otp_error_text()
        if error_otp:
            print(f"[OTP ERROR] {error_otp}")
            print(f"[ASSERT] Expect message contains: '{message}'")
            assert message in error_otp
            return

    print("[SUCCESS] Sign up successful")

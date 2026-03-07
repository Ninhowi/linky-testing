"""
Shared signup flow logic. Used by automation tests (Excel data) and manual tests (user input).
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

from utils.generate_email import generate_email
from utils.safe_input import safe_input


def run_signup_flow(
    driver,
    wait,
    waitAuth,
    first_name,
    last_name,
    email,
    password,
    otp,
    message,
    auto_remove_content,
    auto_remove_content_position,
):
    first_name = first_name or ''
    last_name = last_name or ''
    email = email or ''
    password = password or ''
    otp = otp or ''

    enable_generate_email = True
    if message and (
        "email address already in use" in message
        or "email address is taken" in message
    ):
        print("[INFO] Duplicate email scenario detected → disable email auto-generate")
        enable_generate_email = False

    print("[STEP] Input basic fields")

    first_name_field = wait.until(
        EC.presence_of_element_located((By.NAME, "firstName"))
    )
    print(f"[+] Input First Name: '{first_name}'")
    safe_input(driver, first_name_field, first_name)

    last_name_field = wait.until(
        EC.presence_of_element_located((By.NAME, "lastName"))
    )
    print(f"[+] Input Last Name: '{last_name}'")
    safe_input(driver, last_name_field, last_name)

    email_field = wait.until(
        EC.presence_of_element_located((By.NAME, "emailAddress"))
    )

    final_email = generate_email(
        base_email=email,
        enable_generate_email=enable_generate_email,
        auto_remove_content=auto_remove_content,
        auto_remove_content_position=auto_remove_content_position
    )
    print(f"[+] Input Email (final used): '{final_email}' | auto_generate={enable_generate_email} | auto_remove_content='{auto_remove_content}' | auto_remove_content_position='{auto_remove_content_position}'")
    email_field.send_keys(final_email)

    password_field = wait.until(
        EC.presence_of_element_located((By.NAME, "password"))
    )
    print(f"[+] Input Password: '{password}'")
    password_field.send_keys(password)

    # password length case
    if message and "72 characters" in message:
        print("[BRANCH] Password length validation case")
        error_message = wait.until(
            EC.presence_of_element_located((By.ID, "error-password"))
        ).text.strip()

        print(f"[ERROR TEXT] {error_message}")
        print(f"[ASSERT] Expect message contains: '{message}'")
        assert message in error_message
        return

    # accept legal
    print("[ACTION] Accept legal terms")
    legal_field = wait.until(
        EC.presence_of_element_located((By.NAME, "legalAccepted"))
    )
    legal_field.click()

    print("[ACTION] Submit form (ENTER)")
    password_field.send_keys(Keys.RETURN)

    # browser validation
    is_valid_email = driver.execute_script(
        "return arguments[0].checkValidity();", email_field
    )
    is_valid_password = driver.execute_script(
        "return arguments[0].checkValidity();", password_field
    )

    print(f"[STATE] is_valid_email={is_valid_email}, is_valid_password={is_valid_password}")

    if not is_valid_email:
        validation_email_message = driver.execute_script(
            "return arguments[0].validationMessage;", email_field
        )
        print(f"[VALIDATION MESSAGE - EMAIL] {validation_email_message}")
        print(f"[ASSERT] Expect message contains: '{message}'")
        assert message in validation_email_message
        return

    if not is_valid_password:
        validation_password_message = driver.execute_script(
            "return arguments[0].validationMessage;", password_field
        )
        print(f"[VALIDATION MESSAGE - PASSWORD] {validation_password_message}")
        print(f"[ASSERT] Expect message contains: '{message}'")
        assert message in validation_password_message
        return

    # wait server response
    print("[WAIT] Waiting server response...")

    try:
        wait.until(
            EC.any_of(
                EC.presence_of_element_located((By.ID, "error-firstName")),
                EC.presence_of_element_located((By.ID, "error-lastName")),
                EC.presence_of_element_located((By.ID, "error-emailAddress")),
                EC.presence_of_element_located((By.ID, "error-password")),
                EC.presence_of_element_located((By.CLASS_NAME, "cl-alertText")),
                EC.url_contains("verify-email-address")
            )
        )
    except TimeoutException:
        print("[WARN] Timeout waiting server response")

    # alert error
    alert_elements = driver.find_elements(By.CLASS_NAME, "cl-alertText")
    alert_text = alert_elements[0].text.strip() if alert_elements else ""

    if alert_text:
        print(f"[ALERT ERROR] {alert_text}")
        print(f"[ASSERT] Expect message contains: '{message}'")
        assert message in alert_text
        return

    # inline errors
    error_elements = driver.find_elements(By.CSS_SELECTOR, "[id^='error-']")
    errors_text = " ".join(e.text.strip() for e in error_elements if e.text.strip())

    if errors_text:
        print(f"[INLINE ERRORS] {errors_text}")
        print(f"[ASSERT] Expect message contains: '{message}'")
        assert message in errors_text
        return

    # otp flow
    current_url = driver.current_url
    print(f"[STATE] Current URL: {current_url}")

    if "verify-email-address" in current_url:
        print("[FLOW] OTP verification required")

        otp_field = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@autocomplete='one-time-code']")
            )
        )

        print(f"[+] Input OTP: '{otp}'")
        otp_field.send_keys(otp)

        print("[WAIT] Waiting OTP result...")

        try:
            waitAuth.until(
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

        if "verify-email-address" not in driver.current_url:
            print("[SUCCESS] Sign up successful after OTP")
            waitAuth.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//a[@data-testid='start-chat-button']")
                )
            )
            return

        error_otp_element = driver.find_elements(By.ID, "error-undefined")

        if error_otp_element:
            error_message = error_otp_element[0].text.strip()
            print(f"[OTP ERROR] {error_message}")
            print(f"[ASSERT] Expect message contains: '{message}'")
            assert message in error_message
            return

    print("[SUCCESS] Sign up successful")

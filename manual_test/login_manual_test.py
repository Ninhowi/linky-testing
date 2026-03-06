import time
import pytest as pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from utils.chrome_driver import custom_chrome_driver
from utils.configure import isEnableHeadless

enable_headless = isEnableHeadless()

def test_submit_login_form(email, password, otp, message):
    print("\n" + "=" * 80)
    print(f"[TEST CASE START - LOGIN")
    print(f"[INPUT DATA] email={email}, password={password}, otp={otp}, expected_message={message}")
    print("=" * 80)

    driver = custom_chrome_driver(enable_headless=enable_headless)

    print("[BROWSER] Chrome driver initialized")

    driver.implicitly_wait(1)

    driver.get("https://www.linkynow.site/sign-in")
    print("[NAVIGATION] Opened Sign In page")

    wait = WebDriverWait(driver, 5, poll_frequency=0.2)
    waitAuth = WebDriverWait(driver, 10, poll_frequency=0.2)

    try:
        email = email or ''
        password = password or ''
        otp = otp or ''

        # email step

        print("[STEP] Email step")

        email_field = wait.until(
            EC.presence_of_element_located((By.NAME, "identifier"))
        )

        print(f"[+] Input Email: '{email}'")
        email_field.send_keys(str(email))

        print("[ACTION] Submit email (ENTER)")
        email_field.send_keys(Keys.RETURN)

        # browser validation

        is_valid = driver.execute_script(
            "return arguments[0].checkValidity();",
            email_field
        )

        print(f"[STATE] Browser email valid={is_valid}")

        if not is_valid:
            validation_message = driver.execute_script(
                "return arguments[0].validationMessage;",
                email_field
            )
            print(f"[VALIDATION MESSAGE - EMAIL]: {validation_message}")
            print(f"[ASSERT] Expect message contains: '{message}'")
            assert message in validation_message
            return

        # wait email result

        print("[WAIT] Waiting for email validation result...")

        try:
            wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.ID, "error-identifier")),
                    EC.presence_of_element_located((By.NAME, "password"))
                )
            )
        except TimeoutException:
            print("[WARN] Timeout waiting email result")

        # check email error
        if driver.find_elements(By.ID, "error-identifier"):
            result_message = driver.find_element(By.ID, "error-identifier").text.strip()
            print(f"[!] Email invalid - Error: {result_message}")
            print(f"[ASSERT] Expect message contains: '{message}'")
            assert message in result_message
            return

        print("[+] Email valid -> Go to password step")

        # password step

        password_field = wait.until(
            EC.presence_of_element_located((By.NAME, "password"))
        )

        print(f"[+] Input Password: '{password}'")
        password_field.send_keys(password)

        print("[ACTION] Submit password (ENTER)")
        password_field.send_keys(Keys.RETURN)

        print("[WAIT] Waiting for password validation result...")

        try:
            wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.ID, "error-password")),
                    EC.url_contains("factor-two"),
                    EC.url_contains("linkynow.site")
                )
            )
        except TimeoutException:
            print("[WARN] Timeout waiting password result")

        # check password error
        if driver.find_elements(By.ID, "error-password"):
            result_message = driver.find_element(By.ID, "error-password").text.strip()
            print(f"[!] Password invalid - Error: {result_message}")
            print(f"[ASSERT] Expect message contains: '{message}'")
            assert message in result_message
            return

        print("[+] Password valid")

        # check otp

        current_url = driver.current_url
        print(f"[STATE] Current URL after password: {current_url}")

        if "factor-two" in current_url:

            print("[FLOW] OTP required (new device)")

            otp_field = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[autocomplete='one-time-code']")
                )
            )

            print(f"[+] Input OTP: '{otp}'")
            otp_field.send_keys(otp)

            print("[WAIT] Waiting OTP result...")

            try:
                waitAuth.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CLASS_NAME, "cl-otpCodeFieldSuccessText")),
                        EC.presence_of_element_located((By.ID, "error-undefined")),
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "[data-testid='start-chat-button']")
                        )
                    )
                )
            except TimeoutException:
                print("[WARN] Timeout waiting OTP result")

            # success check first
            if "factor-two" not in driver.current_url:
                print("[SUCCESS] Login successful after OTP")
                waitAuth.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[data-testid='start-chat-button']")
                    )
                )
                return

            error_otp_element = driver.find_elements(By.ID, "error-undefined")

            if error_otp_element:
                error_message = error_otp_element[0].text.strip()
                print(f"[!] OTP invalid - Error: {error_message}")
                print(f"[ASSERT] Expect message contains: '{message}'")
                assert message in error_message
                return

        # login success without OTP or after OTP

        print("[SUCCESS] Login successful")
        waitAuth.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[data-testid='start-chat-button']")
            )
        )

    finally:
        print("[CLEANUP] Closing browser...")
        time.sleep(1)
        driver.quit()
        print("[TEST CASE FINISHED - LOGIN]")


input_email = input("Enter email for login test: ")
input_password = input("Enter password for login test: ")
input_otp = input("Enter OTP for login test (if applicable, otherwise leave blank): ")
expected_message = input("Enter expected error message (if applicable, otherwise leave blank): ")

test_submit_login_form(input_email, input_password, input_otp, expected_message)
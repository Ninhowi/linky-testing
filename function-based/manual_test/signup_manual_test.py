import time
from selenium.webdriver.support.ui import WebDriverWait

from utils.chrome_driver import custom_chrome_driver
from utils.configure import getAutoRemoveContent, getAutoRemoveContentPosition, isEnableHeadless
from core.signup_flow import run_signup_flow

enable_headless = isEnableHeadless()
auto_remove_content = getAutoRemoveContent()
auto_remove_content_position = getAutoRemoveContentPosition()


def test_submit_sign_up_form(first_name, last_name, email, password, otp, message):
    print("\n" + "=" * 100)
    print(f"[TEST CASE START - SIGN UP]")
    print(f"[INPUT DATA] first_name={first_name}, last_name={last_name}, email={email}, password={password}, otp={otp}, expected_message={message}")
    print("=" * 100)

    driver = custom_chrome_driver(enable_headless=enable_headless)
    print("[BROWSER] Chrome driver initialized")

    driver.implicitly_wait(0)

    driver.get("https://www.linkynow.site/sign-up")
    print("[NAVIGATION] Opened Sign Up page")

    wait = WebDriverWait(driver, 5, poll_frequency=0.2)
    waitAuth = WebDriverWait(driver, 10, poll_frequency=0.2)

    try:
        run_signup_flow(
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
        )
    finally:
        print("[CLEANUP] Closing browser...")
        time.sleep(1)
        driver.quit()
        print("[TEST CASE FINISHED - SIGN UP]")


input_first_name = input("Enter first name: ")
input_last_name = input("Enter last name: ")
input_email = input("Enter email: ")
input_password = input("Enter password: ")
input_otp = input("Enter OTP (if applicable, otherwise leave blank): ")
input_message = input("Enter expected message (if applicable, otherwise leave blank): ")

test_submit_sign_up_form(input_first_name, input_last_name, input_email, input_password, input_otp, input_message)

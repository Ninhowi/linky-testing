import time
from selenium.webdriver.support.ui import WebDriverWait

from utils.chrome_driver import custom_chrome_driver
from utils.configure import isEnableHeadless
from core.login_flow import run_login_flow

enable_headless = isEnableHeadless()


def test_submit_login_form(email, password, otp, message):
    print("\n" + "=" * 80)
    print(f"[TEST CASE START - LOGIN]")
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
        run_login_flow(driver, wait, waitAuth, email, password, otp, message)
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

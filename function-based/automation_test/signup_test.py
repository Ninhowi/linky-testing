import time
from pathlib import Path
import openpyxl
import pytest as pytest
from selenium.webdriver.support.ui import WebDriverWait

from utils.chrome_driver import custom_chrome_driver
from utils.configure import getAutoRemoveContent, getAutoRemoveContentPosition, isEnableHeadless
from core.signup_flow import run_signup_flow

# Root testdata (shared with POM)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TESTDATA_DIR = _PROJECT_ROOT / "testdata"

min_row = 2
max_row = 35

enable_headless = isEnableHeadless()

auto_remove_content = getAutoRemoveContent()
auto_remove_content_position = getAutoRemoveContentPosition()


def read_test_data_from_excel(excel_file):
    print(f"[DATA] Loading signup test data from: {excel_file}")

    workbook = openpyxl.load_workbook(excel_file)
    sheet = workbook.active
    test_data = []

    for idx, row in enumerate(
        sheet.iter_rows(min_row=min_row, max_row=max_row, values_only=True),
        start=min_row
    ):
        first_name, last_name, email, password, otp, message = row

        test_data.append(
            pytest.param(
                idx,
                first_name,
                last_name,
                email,
                password,
                otp,
                message,
                id=f"row-{idx}"
            )
        )

    print(f"[DATA] Loaded {len(test_data)} signup test cases")
    return test_data


test_data = read_test_data_from_excel(TESTDATA_DIR / "data_test_signup.xlsx")


@pytest.mark.parametrize("row_index, first_name, last_name, email, password, otp, message", test_data)
def test_submit_sign_up_form(row_index, first_name, last_name, email, password, otp, message):
    print("\n" + "=" * 100)
    print(f"[TEST CASE START - SIGN UP] Row Index: {row_index}")
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

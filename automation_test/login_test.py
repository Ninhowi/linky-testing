import time
import openpyxl
import pytest as pytest
from selenium.webdriver.support.ui import WebDriverWait

from utils.chrome_driver import custom_chrome_driver
from utils.configure import isEnableHeadless
from core.login_flow import run_login_flow

min_row = 2
max_row = 13

enable_headless = isEnableHeadless()


def read_test_data_from_excel(excel_file):
    print(f"[DATA] Loading login test data from: {excel_file}")

    workbook = openpyxl.load_workbook(excel_file)
    sheet = workbook.active
    test_data = []

    for idx, row in enumerate(
        sheet.iter_rows(min_row=min_row, max_row=max_row, values_only=True),
        start=min_row
    ):
        email, password, otp, message = row

        test_data.append(
            pytest.param(
                idx,
                email,
                password,
                otp,
                message,
                id=f"row-{idx}"
            )
        )

    print(f"[DATA] Loaded {len(test_data)} login test cases")
    return test_data


test_data = read_test_data_from_excel('testdata/data_test_login.xlsx')


@pytest.mark.parametrize("row_index, email, password, otp, message", test_data)
def test_submit_login_form(row_index, email, password, otp, message):

    print("\n" + "=" * 80)
    print(f"[TEST CASE START - LOGIN] Row Index: {row_index}")
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

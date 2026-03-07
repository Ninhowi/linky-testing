"""Sign-up tests using POM and Excel data."""
import time
import openpyxl
import pytest
from utils.configure import getAutoRemoveContent, getAutoRemoveContentPosition
from flows.signup_flow import run_signup_flow

MIN_ROW = 2
MAX_ROW = 35


def load_signup_data(excel_path: str = "testdata/data_test_signup.xlsx"):
    workbook = openpyxl.load_workbook(excel_path)
    sheet = workbook.active
    rows = []
    for idx, row in enumerate(
        sheet.iter_rows(min_row=MIN_ROW, max_row=MAX_ROW, values_only=True),
        start=MIN_ROW,
    ):
        first_name, last_name, email, password, otp, message = row
        rows.append(
            pytest.param(
                idx, first_name, last_name, email, password, otp, message,
                id=f"row-{idx}",
            )
        )
    return rows


signup_data = load_signup_data()
auto_remove_content = getAutoRemoveContent()
auto_remove_content_position = getAutoRemoveContentPosition()


@pytest.mark.parametrize(
    "row_index, first_name, last_name, email, password, otp, message",
    signup_data,
)
def test_signup_form(
    row_index,
    first_name,
    last_name,
    email,
    password,
    otp,
    message,
    sign_up_page,
    verify_email_page,
    dashboard_page,
):
    print("\n" + "=" * 100)
    print(f"[TEST CASE START - SIGN UP] Row Index: {row_index}")
    print(f"[INPUT DATA] first_name={first_name}, last_name={last_name}, email={email}, password={password}, otp={otp}, expected_message={message}")
    print("=" * 100)

    sign_up_page.open_sign_up()

    run_signup_flow(
        sign_up_page,
        verify_email_page,
        dashboard_page,
        first_name,
        last_name,
        email,
        password,
        otp,
        message,
        auto_remove_content,
        auto_remove_content_position,
    )

    time.sleep(1)
    print("[TEST CASE FINISHED - SIGN UP]")

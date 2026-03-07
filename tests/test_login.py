"""Login tests using POM and Excel data."""
import time
import openpyxl
import pytest
from flows.login_flow import run_login_flow

MIN_ROW = 2
MAX_ROW = 13


def load_login_data(excel_path: str = "testdata/data_test_login.xlsx"):
    workbook = openpyxl.load_workbook(excel_path)
    sheet = workbook.active
    rows = []
    for idx, row in enumerate(
        sheet.iter_rows(min_row=MIN_ROW, max_row=MAX_ROW, values_only=True),
        start=MIN_ROW,
    ):
        email, password, otp, message = row
        rows.append(
            pytest.param(idx, email, password, otp, message, id=f"row-{idx}")
        )
    return rows


login_data = load_login_data()


@pytest.mark.parametrize("row_index, email, password, otp, message", login_data)
def test_login_form(
    row_index,
    email,
    password,
    otp,
    message,
    sign_in_page,
    verify_email_page,
    dashboard_page,
):
    print("\n" + "=" * 80)
    print(f"[TEST CASE START - LOGIN] Row Index: {row_index}")
    print(f"[INPUT DATA] email={email}, password={password}, otp={otp}, expected_message={message}")
    print("=" * 80)

    sign_in_page.open_sign_in()

    run_login_flow(
        sign_in_page,
        verify_email_page,
        dashboard_page,
        email,
        password,
        otp,
        message,
    )

    time.sleep(1)
    print("[TEST CASE FINISHED - LOGIN]")

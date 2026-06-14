"""Reset-password cases driven by test_data/data.xlsx (sheet: reset_password).

Các test case đặt lại mật khẩu từ test_data/data.xlsx (sheet: reset_password).
"""

from __future__ import annotations

import pytest
from selenium.webdriver.remote.webelement import WebElement

from helpers.auth_excel import (
    assert_auth_outcome,
    case_id,
    cell_value,
    excel_flag,
    load_sheet_cases,
    message_lower,
    reset_password_assert_messages,
    reset_password_should_submit,
    reset_password_steps,
    run_identifier_step,
    run_otp_step,
    run_password_step,
)
from helpers.load_excel import TestRow
from pages.reset_password import ResetPasswordPage

pytestmark = pytest.mark.reset_password

RESET_PASSWORD_CASES = load_sheet_cases("reset_password")


def _run_sign_in_through_otp(page: ResetPasswordPage, case: TestRow) -> None:
    """Same identifier → password → OTP steps as ``test_sign_in``.

    Cùng các bước identifier → password → OTP như ``test_sign_in``.
    """
    steps = reset_password_steps(case)
    email = cell_value(case.get("email"))

    run_identifier_step(page.identifier, email)

    if steps["password"]:
        run_password_step(
            page.password,
            None,
            forgot=True,
            on_forgot=page.forgot.click_reset_your_password,
        )

    if steps["otp"]:
        run_otp_step(page.otp, cell_value(case.get("otp")))


def _run_reset_password_flow(page: ResetPasswordPage, case: TestRow) -> None:
    steps = reset_password_steps(case)

    _run_sign_in_through_otp(page, case)

    if steps["reset"]:
        page.reset.wait_until_visible()
        new_password = cell_value(case.get("new_password"))
        confirm_password = cell_value(case.get("confirm_password"))
        page.reset.fill_passwords(new_password, confirm_password)
        sign_out = excel_flag(case, "log_out")
        if sign_out is not None:
            page.reset.set_sign_out_all_devices(sign_out)
        if reset_password_should_submit(case):
            page.reset.submit()


def _field_for_assertion(page: ResetPasswordPage, case: TestRow) -> WebElement:
    """Pick the input field most likely tied to the expected error.

    Chọn trường input khả năng cao nhất liên quan đến lỗi mong đợi.
    """
    message = message_lower(case)
    steps = reset_password_steps(case)

    if "code" in message or (steps["otp"] and cell_value(case.get("otp"))):
        return page.otp.otp_input()
    if "match" in message or (
        steps["reset"] and cell_value(case.get("confirm_password"))
    ):
        return page.reset.confirm_password_input()
    if steps["reset"] and cell_value(case.get("new_password")):
        return page.reset.new_password_input()
    return page.otp.otp_input()


@pytest.mark.parametrize(
    "reset_case",
    RESET_PASSWORD_CASES,
    ids=[
        case_id("reset", i, row) for i, row in enumerate(RESET_PASSWORD_CASES)
    ],
)
def test_reset_password_from_excel(
    driver, base_url: str, reset_case: TestRow
) -> None:
    """Each ``reset_password`` sheet row: sign-in → forgot → OTP → reset form.

    Mỗi dòng sheet ``reset_password``: đăng nhập → quên mật khẩu → OTP → form đặt lại.
    """
    page = ResetPasswordPage.open(driver, base_url)
    _run_reset_password_flow(page, reset_case)
    assert_auth_outcome(
        page,
        driver,
        reset_case,
        field_for_assertion=_field_for_assertion,
        auth_path="/sign-in",
        messages=reset_password_assert_messages(reset_case),
        wait_timeout=25,
    )

"""Sign-up cases driven by test_data/data.xlsx (sheet: sign_up).

Các test case đăng ký từ test_data/data.xlsx (sheet: sign_up).
"""

from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from helpers.auth_excel import (
    assert_auth_outcome,
    case_id,
    cell_value,
    load_sheet_cases,
    message_lower,
    run_otp_step,
    sign_up_assert_messages,
    sign_up_email,
    sign_up_steps,
)
from helpers.load_excel import TestRow
from pages.sign_up import SignUpPage

pytestmark = pytest.mark.sign_up

SIGN_UP_CASES = load_sheet_cases("sign_up")


def _run_sign_up_flow(page: SignUpPage, case: TestRow) -> None:
    steps = sign_up_steps(case)
    email = sign_up_email(case) if steps["email"] else None
    password = cell_value(case.get("password")) if steps["password"] else None

    page.form.fill(email, password, accept_legal=steps["legal"])
    page.form.submit()

    if steps["otp"]:
        run_otp_step(page.otp, cell_value(case.get("otp")))


def _field_for_assertion(page: SignUpPage, case: TestRow) -> WebElement:
    """Pick the input field most likely tied to the expected error.

    Chọn trường input khả năng cao nhất liên quan đến lỗi mong đợi.
    """
    message = message_lower(case)
    steps = sign_up_steps(case)

    if "code" in message or steps["otp"]:
        return page.otp.otp_input()
    if "password" in message or (steps["password"] and cell_value(case.get("password"))):
        return page.form.password_input()
    if "check this box" in message or "procced" in message:
        return page.form.legal_input()
    return page.form.email_input()


@pytest.mark.parametrize(
    "sign_up_case",
    SIGN_UP_CASES,
    ids=[case_id("signup", i, row) for i, row in enumerate(SIGN_UP_CASES)],
)
def test_sign_up_from_excel(driver, base_url: str, sign_up_case: TestRow) -> None:
    """Each ``sign_up`` sheet row: registration form / otp inputs and ``message`` assertion.

    Mỗi dòng sheet ``sign_up``: nhập form đăng ký / OTP và kiểm tra ``message``.
    """
    page = SignUpPage.open(driver, base_url)
    _run_sign_up_flow(page, sign_up_case)
    assert_auth_outcome(
        page,
        driver,
        sign_up_case,
        field_for_assertion=_field_for_assertion,
        auth_path="/sign-up",
        messages=sign_up_assert_messages(sign_up_case),
    )

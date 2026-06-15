"""Sign-in cases driven by test_data/data.xlsx (sheet: login).

Các test case đăng nhập từ test_data/data.xlsx (sheet: login).
"""

from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from helpers.auth.excel import (
    assert_auth_outcome,
    run_identifier_step,
    run_otp_step,
    run_password_step,
    sign_in_steps,
)
from helpers.excel.cells import case_id, cell_value, load_sheet_cases, message_lower
from helpers.excel.load import TestRow
from pages.sign_in import SignInPage

pytestmark = pytest.mark.sign_in

LOGIN_CASES = load_sheet_cases("login")


def _run_login_flow(page: SignInPage, case: TestRow) -> None:
    steps = sign_in_steps(case)
    email = cell_value(case.get("email"))
    password = cell_value(case.get("password"))

    run_identifier_step(page.identifier, email)

    if steps["password"]:
        run_password_step(page.password, password)

    if steps["otp"]:
        run_otp_step(page.otp, cell_value(case.get("otp")))


def _field_for_assertion(page: SignInPage, case: TestRow) -> WebElement:
    """Pick the input field most likely tied to the expected error.

    Chọn trường input khả năng cao nhất liên quan đến lỗi mong đợi.
    """
    message = message_lower(case)
    steps = sign_in_steps(case)

    if "code" in message or (steps["otp"] and cell_value(case.get("otp"))):
        return page.otp.otp_input()
    if "password" in message or (steps["password"] and cell_value(case.get("password"))):
        return page.password.password_input()
    return page.identifier.email_input()


@pytest.mark.parametrize(
    "login_case",
    LOGIN_CASES,
    ids=[case_id("login", i, row) for i, row in enumerate(LOGIN_CASES)],
)
def test_sign_in_from_excel(driver, base_url: str, login_case: TestRow) -> None:
    """Each ``login`` sheet row: email / password / otp inputs and ``message`` assertion.

    Mỗi dòng sheet ``login``: nhập email / password / OTP và kiểm tra ``message``.
    """
    page = SignInPage.open(driver, base_url)
    _run_login_flow(page, login_case)
    assert_auth_outcome(
        page,
        driver,
        login_case,
        field_for_assertion=_field_for_assertion,
        auth_path="/sign-in",
    )

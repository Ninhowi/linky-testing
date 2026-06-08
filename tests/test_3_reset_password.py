"""Reset-password cases driven by test_data/data.xlsx (sheet: reset_password)."""

from __future__ import annotations

import time

import pytest
from selenium.webdriver.remote.webelement import WebElement

from helpers.auth_excel import (
    assert_auth_outcome,
    case_id,
    cell_value,
    load_sheet_cases,
    log_out_all_devices,
    message_lower,
    otp_is_complete,
    otp_text,
    password_text,
    reset_password_assert_messages,
    reset_password_should_submit,
    reset_password_steps,
)
from helpers.load_excel import TestRow
from pages.reset_password import ResetPasswordPage

pytestmark = pytest.mark.reset_password

RESET_PASSWORD_CASES = load_sheet_cases("reset_password")

_VALIDATION_TRANSITION_SEC = 0.3


def _run_sign_in_through_otp(page: ResetPasswordPage, case: TestRow) -> None:
    """Same identifier → password → OTP steps as ``test_sign_in``."""
    steps = reset_password_steps(case)
    email = cell_value(case.get("email"))
    otp = otp_text(case.get("otp"))

    if email:
        page.identifier.submit_email(email)
    else:
        page.identifier.submit_empty()

    if steps["password"]:
        page.password.wait_until_visible()
        page.password.click_forgot_password()
        page.forgot.click_reset_your_password()

    if steps["otp"]:
        page.otp.wait_until_visible()
        if otp:
            page.otp.fill_otp(otp)
        if not otp_is_complete(otp):
            page.otp.continue_button().click()


def _run_reset_password_flow(page: ResetPasswordPage, case: TestRow) -> None:
    steps = reset_password_steps(case)

    _run_sign_in_through_otp(page, case)

    if steps["reset"]:
        page.reset.wait_until_visible()
        new_password = password_text(case.get("new_password"))
        confirm_password = password_text(case.get("confirm_password"))
        page.reset.fill_passwords(new_password, confirm_password)
        if not reset_password_should_submit(case):
            time.sleep(_VALIDATION_TRANSITION_SEC)
        sign_out = log_out_all_devices(case)
        if sign_out is not None:
            page.reset.set_sign_out_all_devices(sign_out)
        if reset_password_should_submit(case):
            page.reset.submit()


def _field_for_assertion(page: ResetPasswordPage, case: TestRow) -> WebElement:
    """Pick the input field most likely tied to the expected error."""
    message = message_lower(case)
    steps = reset_password_steps(case)

    if "code" in message or (steps["otp"] and otp_text(case.get("otp"))):
        return page.otp.otp_input()
    if "match" in message or (
        steps["reset"] and password_text(case.get("confirm_password"))
    ):
        return page.reset.confirm_password_input()
    if steps["reset"] and password_text(case.get("new_password")):
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
    """Each ``reset_password`` sheet row: sign-in → forgot → OTP → reset form."""
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

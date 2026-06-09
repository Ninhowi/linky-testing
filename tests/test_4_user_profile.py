"""User-profile cases driven by test_data/data.xlsx (sheet: profile)."""

from __future__ import annotations

import pytest

from helpers.auth_excel import case_id, load_sheet_cases
from helpers.load_excel import TestRow
from helpers.profile_excel import fields_to_fill, section_name
from helpers.profile_validation import (
    assert_profile_field_error,
    assert_profile_outcome,
    profile_combobox_not_found_messages,
    profile_expects_inline_field_error,
)
from pages.user_profile import UserProfilePage

pytestmark = [pytest.mark.profile, pytest.mark.xdist_group("profile")]

PROFILE_CASES = load_sheet_cases("profile")


def _run_profile_flow(page: UserProfilePage, case: TestRow) -> None:
    section = section_name(case)
    page.edit_section(section)
    page.fill_fields(
        section,
        fields_to_fill(case, section),
        not_found_messages=profile_combobox_not_found_messages(case),
    )
    page.click_save_section(section)
    if profile_expects_inline_field_error(case):
        assert_profile_field_error(page, case)
    page.wait_save_section(
        section,
        stop_on_field_error=profile_expects_inline_field_error(case),
    )


@pytest.mark.parametrize(
    "profile_case",
    PROFILE_CASES,
    ids=[case_id("profile", i, row) for i, row in enumerate(PROFILE_CASES)],
)
def test_profile_from_excel(
    profile_driver, base_url: str, profile_case: TestRow
) -> None:
    """Each ``profile`` sheet row: edit section, fill fields, save, assert outcome."""
    page = UserProfilePage(profile_driver)
    profile_driver.get(f"{base_url.rstrip('/')}{UserProfilePage.PATH}")
    page.wait_until_ready(profile_driver)
    _run_profile_flow(page, profile_case)
    assert_profile_outcome(page, profile_case)

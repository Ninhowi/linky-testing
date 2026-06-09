"""User-profile cases driven by test_data/data.xlsx (sheet: profile)."""

from __future__ import annotations

import pytest

from helpers.auth_excel import case_id, cell_text, load_sheet_cases
from helpers.load_excel import TestRow
from helpers.profile_excel import fields_to_fill, section_name
from pages.user_profile import UserProfilePage

pytestmark = [pytest.mark.profile, pytest.mark.xdist_group("profile")]

PROFILE_CASES = load_sheet_cases("profile")


def _run_profile_flow(page: UserProfilePage, case: TestRow) -> None:
    section = section_name(case)
    page.edit_section(section)
    page.fill_fields(section, fields_to_fill(case, section))
    page.save_section(section)


@pytest.mark.parametrize(
    "profile_case",
    PROFILE_CASES,
    ids=[case_id("profile", i, row) for i, row in enumerate(PROFILE_CASES)],
)
def test_profile_from_excel(
    profile_driver, base_url: str, profile_case: TestRow
) -> None:
    """Each ``profile`` sheet row: edit section, fill fields, save, assert toast."""
    page = UserProfilePage(profile_driver)
    profile_driver.get(f"{base_url.rstrip('/')}{UserProfilePage.PATH}")
    page.wait_until_ready(profile_driver)
    _run_profile_flow(page, profile_case)
    page.assert_toast(cell_text(profile_case.get("message")))

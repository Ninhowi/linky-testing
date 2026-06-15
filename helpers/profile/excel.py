"""Excel helpers for user-profile test cases.

Các hàm hỗ trợ Excel cho test case hồ sơ người dùng.
"""

from __future__ import annotations

from datetime import date, datetime

from helpers.excel.cells import cell_input, cell_value, message_lower
from helpers.excel.load import TestRow

PROFILE_SECTIONS = frozenset({"profile-header", "bio", "personal", "interests"})

SECTION_FIELDS: dict[str, tuple[str, ...]] = {
    "profile-header": ("first_name", "last_name", "country"),
    "bio": ("bio",),
    "personal": ("date", "gender"),
    "interests": ("interest",),
}

_COLUMN_TO_SECTION: dict[str, str] = {
    column: section
    for section, columns in SECTION_FIELDS.items()
    for column in columns
}


def profile_cell_text(value: object) -> str | None:
    """Resolve a profile sheet cell to text, formatting dates as ``DD/MM/YYYY``.

    Chuyển ô sheet profile thành văn bản, định dạng ngày ``DD/MM/YYYY``.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    text = cell_input(value)
    return text if text else None


def _case_has_value(case: TestRow, column: str) -> bool:
    return column in case and case[column] is not None


def _section_from_message(case: TestRow) -> str | None:
    message = message_lower(case)
    if not message:
        return None
    if "bio" in message:
        return "bio"
    if any(
        phrase in message
        for phrase in (
            "first name",
            "last name",
            "profile updated",
            "invalid characters",
            "256",
        )
    ):
        return "profile-header"
    if "personal information" in message or "date of birth" in message:
        return "personal"
    if "interest" in message or "tag" in message:
        return "interests"
    return None


def section_name(case: TestRow) -> str:
    explicit = cell_value(case.get("section"))
    if explicit and explicit in PROFILE_SECTIONS:
        return explicit

    for section, columns in SECTION_FIELDS.items():
        if any(_case_has_value(case, column) for column in columns):
            return section

    inferred = _section_from_message(case)
    if inferred is not None:
        return inferred

    raise ValueError(
        "Could not infer profile section from row data. "
        f"Columns with values: {[column for column in _COLUMN_TO_SECTION if _case_has_value(case, column)]}"
    )


def fields_to_fill(case: TestRow, section: str) -> list[tuple[str, str]]:
    """Return ``(column, value)`` pairs for non-``None`` cells in the section.

    Trả về các cặp ``(cột, giá trị)`` cho ô không ``None`` trong section.
    """
    columns = SECTION_FIELDS[section]
    fields: list[tuple[str, str]] = []
    for column in columns:
        if column not in case or case[column] is None:
            continue
        fields.append((column, profile_cell_text(case[column]) or ""))

    message = message_lower(case)
    if (
        section == "profile-header"
        and "first name cannot be empty" in message
        and not any(column == "first_name" for column, _ in fields)
    ):
        fields.insert(0, ("first_name", ""))

    return fields

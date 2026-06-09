"""Excel helpers for user-profile test cases."""

from __future__ import annotations

from datetime import date, datetime

from helpers.auth_excel import cell_value
from helpers.load_excel import TestRow

PROFILE_SECTIONS = frozenset({"profile-header", "bio", "personal", "interests"})

SECTION_FIELDS: dict[str, tuple[str, ...]] = {
    "profile-header": ("first_name", "last_name", "country"),
    "bio": ("bio",),
    "personal": ("date", "gender"),
    "interests": ("interest",),
}


def profile_cell_text(value: object) -> str | None:
    """Resolve a profile sheet cell to text, formatting dates as ``DD/MM/YYYY``."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    return str(value)


def section_name(case: TestRow) -> str:
    name = cell_value(case.get("section"))
    if not name or name not in PROFILE_SECTIONS:
        raise ValueError(
            f"Invalid profile section {name!r}; expected one of {sorted(PROFILE_SECTIONS)}"
        )
    return name


def fields_to_fill(case: TestRow, section: str) -> list[tuple[str, str]]:
    """Return ``(column, value)`` pairs for non-``None`` cells in the section."""
    columns = SECTION_FIELDS[section]
    fields: list[tuple[str, str]] = []
    for column in columns:
        if column not in case or case[column] is None:
            continue
        fields.append((column, profile_cell_text(case[column]) or ""))
    return fields

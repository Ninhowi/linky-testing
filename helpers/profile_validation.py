"""Profile save outcome assertions (field errors + toast).

Các assertion kết quả lưu profile (lỗi trường + toast).
"""

from __future__ import annotations

import re

from helpers.auth_excel import cell_text, message_lower
from helpers.load_excel import TestRow
from helpers.profile_excel import SECTION_FIELDS, fields_to_fill, section_name
from pages.user_profile import UserProfilePage

_COMBOBOX_COLUMNS = frozenset({"country", "gender", "interest"})
_COMBOBOX_NOT_FOUND_MESSAGE = re.compile(r"no .+ found", re.I)

_VALIDATION_HINTS = (
    "cannot",
    "must",
    "should not",
    "invalid",
    "no tags",
    "not found",
    "unexpected token",
    "not valid",
    "too long",
    "exceed",
)


def profile_combobox_not_found_messages(case: TestRow) -> list[str]:
    """Messages for combobox empty states like ``No tags found.``.

    Thông báo khi combobox trống như ``No tags found.``.
    """
    return [
        message
        for message in profile_assert_messages(case)
        if _COMBOBOX_NOT_FOUND_MESSAGE.search(message)
    ]


def profile_assert_messages(case: TestRow) -> list[str]:
    """Messages that may appear for a profile row (primary + known UI variants).

    Các thông báo có thể xuất hiện ở dòng profile (chính + các biến thể UI đã biết).
    """
    message = cell_text(case.get("message"))
    if not message:
        return []

    messages = [message]
    lower = message.lower()

    if "256" in lower and "first name" in lower:
        messages.append("Name must be 256 characters or fewer.")

    if "300" in lower and "bio" in lower:
        messages.append("Bio must be 300 characters or fewer.")

    return list(dict.fromkeys(messages))


def profile_expects_field_error(case: TestRow) -> bool:
    """Return whether the row expects a validation outcome (field and/or toast).

    Trả về dòng có mong đợi kết quả xác thực (trường và/hoặc toast) hay không.
    """
    message = message_lower(case)
    return any(hint in message for hint in _VALIDATION_HINTS)


def profile_expects_inline_field_error(case: TestRow) -> bool:
    """Return whether the row expects an error under the form field (not toast-only).

    Trả về dòng có mong đợi lỗi dưới trường form (không chỉ toast) hay không.
    """
    message = message_lower(case)
    if not profile_expects_field_error(case):
        return False
    if _COMBOBOX_NOT_FOUND_MESSAGE.search(message):
        return False
    return "unexpected token" not in message


def profile_field_for_message(case: TestRow) -> str | None:
    """Pick the column whose inline error is most likely tied to ``message``.

    Chọn cột có lỗi inline khả năng cao nhất liên quan đến ``message``.
    """
    message = message_lower(case)
    section = section_name(case)

    if "invalid characters" in message:
        for column, _ in fields_to_fill(case, section):
            if column in ("first_name", "last_name"):
                return column
        return "first_name"
    if "first name" in message:
        return "first_name"
    if "last name" in message:
        return "last_name"
    if "date" in message or "birth" in message:
        return "date"
    if _COMBOBOX_NOT_FOUND_MESSAGE.search(message):
        for column, _ in fields_to_fill(case, section):
            if column in _COMBOBOX_COLUMNS:
                return column
    if "tag" in message:
        return "interest"
    if "country" in message:
        return "country"
    if "gender" in message:
        return "gender"
    if "bio" in message or (section == "bio" and "300" in message):
        return "bio"

    filled = fields_to_fill(case, section)
    if filled:
        return filled[-1][0]
    return SECTION_FIELDS[section][0] if SECTION_FIELDS[section] else None


def assert_profile_field_error(page: UserProfilePage, case: TestRow) -> None:
    """Assert inline field error for validation rows (priority over toast).

    Kiểm tra lỗi inline trường cho dòng xác thực (ưu tiên hơn toast).
    """
    if not profile_expects_inline_field_error(case):
        return
    messages = profile_assert_messages(case)
    if not messages:
        return
    column = profile_field_for_message(case)
    if column is None:
        return
    page.assert_field_error(section_name(case), column, messages)


def assert_profile_toast(page: UserProfilePage, case: TestRow) -> None:
    """Assert the toast message for a profile row.

    Kiểm tra thông báo toast cho dòng profile.
    """
    messages = profile_assert_messages(case)
    if messages:
        page.assert_toast(messages)


def profile_expects_toast(case: TestRow) -> bool:
    """Return whether a toast is expected (some rows are field-error only).

    Trả về có mong đợi toast hay không (một số dòng chỉ có lỗi trường).
    """
    message = message_lower(case)
    if not message:
        return False
    if profile_expects_inline_field_error(case) and "bio must" in message and "300" in message:
        return False
    return True


def assert_profile_outcome(page: UserProfilePage, case: TestRow) -> None:
    """Assert toast after save has finished (field errors asserted earlier).

    Kiểm tra toast sau khi lưu xong (lỗi trường đã kiểm tra trước).
    """
    if profile_expects_toast(case):
        assert_profile_toast(page, case)

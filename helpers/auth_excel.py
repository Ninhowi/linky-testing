"""Shared helpers for Excel-driven auth flow tests.

Các hàm hỗ trợ dùng chung cho các bài test luồng xác thực dựa trên Excel.
"""

from __future__ import annotations

import re
import secrets
import string
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from helpers.load_excel import TestRow, load_excel
from helpers.validation import assert_input_and_screen_message
from helpers.waits import left_auth_url

from pages.clerk_form import OTPStep

ROOT = Path(__file__).resolve().parents[1]
DATA_XLSX = ROOT / "test_data" / "data.xlsx"

_CLERK_TEST_EMAIL = re.compile(r"^(?P<name>.+?)\+clerk_test(?:@(?P<domain>.+))?$")
_RANDOM_SUFFIX_ALPHABET = string.ascii_lowercase + string.digits

PASSWORD_VALIDATION_TRANSITION_SEC = 2.0
_PASSWORD_TRANSITION_POLL_SEC = 0.1

OTP_LENGTH = 6


def load_sheet_cases(sheet: str, *, path: Path = DATA_XLSX) -> list[TestRow]:
    """Load test rows for one sheet from the default or given Excel workbook.

    Nạp các dòng test cho một sheet từ workbook Excel mặc định hoặc chỉ định.
    """
    workbook = load_excel(path)
    cases = workbook.get(sheet)
    if cases is None:
        available = ", ".join(workbook) or "(none)"
        raise ValueError(
            f"Sheet {sheet!r} not found in {path.name}. "
            f"Available sheets: {available}"
        )
    return cases


def cell_input(value: object) -> str:
    """Cell content as string; leading/trailing spaces are kept for form input.

    Nội dung ô dưới dạng chuỗi; giữ nguyên khoảng trắng đầu/cuối khi nhập form.
    """
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    return str(value)


def cell_text(value: object) -> str:
    """Trimmed cell text for messages, flags, and other non-input fields.

    Văn bản ô đã cắt khoảng trắng, dùng cho thông báo, cờ và các trường không phải nhập liệu.
    """
    return cell_input(value).strip()


def cell_value(value: object) -> str | None:
    """Return cell text, or ``None`` when the cell is empty.

    Trả về văn bản ô, hoặc ``None`` khi ô trống.
    """
    text = cell_input(value)
    return text if text != "" else None


def otp_is_complete(otp: str | None, *, length: int = OTP_LENGTH) -> bool:
    """Return whether ``otp`` has the full number of digits expected by Clerk.

    Trả về ``otp`` đã đủ số chữ số mà Clerk yêu cầu hay chưa.
    """
    if not otp:
        return False
    return len(otp) >= length


def excel_flag(case: TestRow, column: str) -> bool | None:
    """Parse a 0/1 Excel flag column; ``None`` when the cell is empty.

    Phân tích cột cờ 0/1 trong Excel; ``None`` khi ô trống.
    """
    value = case.get(column)
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return cell_text(value) not in ("0", "false", "no", "")


def term_accepted(case: TestRow) -> bool:
    """Return whether the legal checkbox should be checked (``term`` column: 1=yes, 0=no).

    Trả về có nên chọn checkbox điều khoản hay không (cột ``term``: 1=có, 0=không).
    """
    return excel_flag(case, "term") or False


def _random_suffix(length: int = 6) -> str:
    return "".join(secrets.choice(_RANDOM_SUFFIX_ALPHABET) for _ in range(length))


def uniquify_clerk_test_email(email: str, *, suffix_length: int = 6) -> str:
    """Turn ``name+clerk_test@domain`` into ``name<random>+clerk_test@domain``.

    Biến ``name+clerk_test@domain`` thành ``name<ngẫu_nhiên>+clerk_test@domain``.
    """
    match = _CLERK_TEST_EMAIL.fullmatch(email.strip())
    if match is None:
        return email
    name = match.group("name")
    domain = match.group("domain")
    local = f"{name}{_random_suffix(suffix_length)}+clerk_test"
    return f"{local}@{domain}" if domain else local


def should_uniquify_sign_up_email(case: TestRow, email: str) -> bool:
    """Only mutate emails that match the clerk_test template and are meant to be valid.

    Chỉ thay đổi email khớp mẫu clerk_test và được coi là hợp lệ.
    """
    if _CLERK_TEST_EMAIL.fullmatch(email.strip()) is None:
        return False
    if " " in email.split("@", 1)[0]:
        return False

    message = message_lower(case)
    return not any(
        phrase in message
        for phrase in (
            "match the requested format",
            "valid email",
            "email address is taken",
            "taken. please try another",
        )
    )


def sign_up_email(case: TestRow) -> str | None:
    """Resolve the sign-up email from Excel, uniquified when the case needs a fresh address.

    Lấy email đăng ký từ Excel, làm duy nhất khi test case cần địa chỉ mới.
    """
    raw = cell_value(case.get("email"))
    if raw is None:
        return None
    if should_uniquify_sign_up_email(case, raw):
        return uniquify_clerk_test_email(raw)
    return raw


def sign_up_assert_messages(case: TestRow) -> list[str]:
    """Messages that may appear for a sign-up row (primary + known Clerk/HTML5 variants).

    Các thông báo có thể xuất hiện ở dòng đăng ký (chính + các biến thể Clerk/HTML5 đã biết).
    """
    message = cell_text(case.get("message"))
    if not message:
        return []

    messages = [message]
    email = cell_value(case.get("email"))
    local = email.split("@", 1)[0] if email else ""

    if " " in local and "valid email" in message_lower(case):
        return ["Please fill out this field", message]

    return messages


def case_id(prefix: str, index: int, case: TestRow) -> str:
    """Build a stable pytest parametrize id from prefix, row index, and message.

    Tạo id pytest parametrize ổn định từ prefix, chỉ số dòng và message.
    """
    message = cell_text(case.get("message"))
    if message:
        return f"{prefix}-{index + 1}-{message[:40]}"
    return f"{prefix}-{index + 1}-pass"


def message_lower(case: TestRow) -> str:
    """Return the row ``message`` column in lowercase.

    Trả về cột ``message`` của dòng ở dạng chữ thường.
    """
    return cell_text(case.get("message")).lower()


def sign_in_steps(case: TestRow) -> dict[str, bool]:
    """Decide how far the sign-in flow runs before asserting ``message``.

    Quyết định luồng đăng nhập chạy đến đâu trước khi kiểm tra ``message``.
    """
    message = cell_text(case.get("message"))
    if not message:
        return {"email": True, "password": True, "otp": True}

    lower = message_lower(case)
    if "code" in lower:
        return {"email": True, "password": True, "otp": True}
    if "password" in lower:
        return {"email": True, "password": True, "otp": False}
    return {"email": True, "password": False, "otp": False}


def reset_password_steps(case: TestRow) -> dict[str, bool]:
    """Decide how far the reset-password flow runs before asserting ``message``.

    Uses the same step keys as ``sign_in_steps`` for the sign-in portion
    (``password`` = password page with forgot-password link, then OTP).

    Quyết định luồng đặt lại mật khẩu chạy đến đâu trước khi kiểm tra ``message``.
    Dùng cùng khóa bước với ``sign_in_steps`` cho phần đăng nhập
    (``password`` = trang mật khẩu có liên kết quên mật khẩu, rồi OTP).
    """
    message = cell_text(case.get("message"))
    if not message:
        return {"email": True, "password": True, "otp": True, "reset": True}

    lower = message_lower(case)
    reset = not ("incorrect code" in lower or "enter code" in lower)
    return {"email": True, "password": True, "otp": True, "reset": reset}


def reset_password_should_submit(case: TestRow) -> bool:
    """Return whether to click Reset Password (``submit``: 1=yes, 0=no).

    Trả về có nên nhấn Đặt lại mật khẩu hay không (``submit``: 1=có, 0=không).
    """
    submit = excel_flag(case, "button")
    if submit is not None:
        return submit
    return True


def reset_password_assert_messages(case: TestRow) -> list[str]:
    """Messages that may appear for a reset-password row.

    Các thông báo có thể xuất hiện ở dòng đặt lại mật khẩu.
    """
    message = cell_text(case.get("message"))
    if not message:
        return []

    messages = [message]
    lower = message_lower(case)

    if "successfully changed" in lower:
        messages.append("Your password was successfully changed")
    if "not strong enough" in lower:
        messages.append("Your password is not strong enough")
    if "could be stronger" in lower:
        messages.append("Your password works, but could be stronger")

    return messages


def sign_up_steps(case: TestRow) -> dict[str, bool]:
    """Decide how far the sign-up flow runs before asserting ``message``.

    Quyết định luồng đăng ký chạy đến đâu trước khi kiểm tra ``message``.
    """
    message = cell_text(case.get("message"))
    email = cell_value(case.get("email"))
    password = cell_value(case.get("password"))
    legal = term_accepted(case)

    if not message:
        return {"email": True, "password": True, "legal": legal, "otp": True}

    lower = message_lower(case)

    if "code" in lower:
        return {"email": True, "password": True, "legal": legal, "otp": True}

    if "check this box" in lower or "procced" in lower:
        return {"email": True, "password": True, "legal": legal, "otp": False}

    if "fill out this field" in lower:
        return {
            "email": bool(email),
            "password": bool(password),
            "legal": legal,
            "otp": False,
        }

    if "password" in lower:
        return {"email": True, "password": True, "legal": legal, "otp": False}

    if any(
        phrase in lower
        for phrase in (
            "match the requested format",
            "valid email",
            "email address is taken",
            "taken. please try another",
        )
    ):
        return {"email": True, "password": True, "legal": legal, "otp": False}

    return {
        "email": bool(email),
        "password": bool(password),
        "legal": legal,
        "otp": False,
    }


def run_identifier_step(identifier: Any, email: str | None) -> None:
    """Submit the identifier step with or without an email value."""
    if email:
        identifier.submit_email(email)
    else:
        identifier.submit_empty()


def run_password_step(
    password_page: Any,
    password_value: str | None,
    *,
    forgot: bool = False,
    on_forgot: Callable[[], None] | None = None,
) -> None:
    """Submit the password step, or follow the forgot-password path."""
    password_page.wait_until_visible()
    if forgot:
        password_page.click_forgot_password()
        if on_forgot is not None:
            on_forgot()
        return
    if password_value:
        password_page.submit_password(password_value)
    else:
        password_page.submit_empty()


def run_otp_step(otp_step: OTPStep, otp: str | None) -> None:
    """Fill OTP when provided and click Continue when the code is incomplete."""
    otp_step.wait_until_visible()
    if otp:
        otp_step.fill_otp(otp)
    if not otp_is_complete(otp):
        otp_step.continue_button().click()


def auth_case_involves_password_form(case: TestRow) -> bool:
    """Return whether the case expects a password-field validation message.

    Trả về test case có mong đợi thông báo xác thực trường mật khẩu hay không.
    """
    if "password" in message_lower(case):
        return True
    for key in ("password", "new_password", "confirm_password"):
        if cell_value(case.get(key)):
            return True
    return False


def wait_password_validation_transition(
    driver: WebDriver,
    page: Any,
    case: TestRow,
    *,
    field_for_assertion: Callable[[Any, TestRow], WebElement],
    messages: list[str],
) -> None:
    """Wait for Clerk password validation text to finish animating in.

    Chờ văn bản xác thực mật khẩu của Clerk hoàn tất hiệu ứng chuyển động.
    """
    if not auth_case_involves_password_form(case):
        return

    from helpers.validation import _auth_message_visible

    resolve_field = lambda: field_for_assertion(page, case)
    deadline = time.monotonic() + PASSWORD_VALIDATION_TRANSITION_SEC
    while time.monotonic() < deadline:
        for message in messages:
            if _auth_message_visible(driver, resolve_field, message):
                return
        time.sleep(_PASSWORD_TRANSITION_POLL_SEC)


def assert_auth_outcome(
    page: Any,
    driver: WebDriver,
    case: TestRow,
    *,
    field_for_assertion: Callable[[Any, TestRow], WebElement],
    auth_path: str,
    wait_timeout: float = 20,
    messages: list[str] | None = None,
) -> None:
    """Assert expected auth messages or wait until the auth flow completes.

    Kiểm tra thông báo xác thực mong đợi hoặc chờ đến khi luồng xác thực hoàn tất.
    """
    expected_messages = messages or [cell_text(case.get("message"))]
    expected_messages = [msg for msg in expected_messages if msg]

    if expected_messages:
        wait_password_validation_transition(
            driver,
            page,
            case,
            field_for_assertion=field_for_assertion,
            messages=expected_messages,
        )
        resolve_field = lambda: field_for_assertion(page, case)
        errors: list[str] = []
        for message in expected_messages:
            try:
                assert_input_and_screen_message(driver, resolve_field, message)
                return
            except (AssertionError, TimeoutException) as exc:
                errors.append(f"{message!r}: {exc}")
        raise AssertionError(
            "Expected message not found. Tried:\n" + "\n".join(errors)
        )

    WebDriverWait(driver, wait_timeout).until(
        lambda _: left_auth_url(driver, auth_path)
    )

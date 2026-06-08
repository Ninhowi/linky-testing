"""Shared helpers for Excel-driven auth flow tests."""

from __future__ import annotations

import re
import secrets
import string
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from helpers.load_excel import TestRow, load_excel
from helpers.validation import assert_input_and_screen_message

ROOT = Path(__file__).resolve().parents[1]
DATA_XLSX = ROOT / "test_data" / "data.xlsx"

_CLERK_TEST_EMAIL = re.compile(r"^(?P<name>.+?)\+clerk_test(?:@(?P<domain>.+))?$")
_RANDOM_SUFFIX_ALPHABET = string.ascii_lowercase + string.digits


class AuthPage(Protocol):
    def assert_input_and_screen_message(
        self,
        input_el: WebElement,
        text: str,
        *,
        exact: bool = False,
        timeout: float = 10,
    ) -> None: ...


def load_sheet_cases(sheet: str, *, path: Path = DATA_XLSX) -> list[TestRow]:
    workbook = load_excel(path)
    cases = workbook.get(sheet)
    if cases is None:
        available = ", ".join(workbook) or "(none)"
        raise ValueError(
            f"Sheet {sheet!r} not found in {path.name}. "
            f"Available sheets: {available}"
        )
    return cases


def cell_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def cell_value(value: object) -> str | None:
    text = cell_text(value)
    return text or None


def otp_text(value: object) -> str | None:
    if value is None or cell_text(value) == "":
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return cell_text(value)


def password_text(value: object) -> str | None:
    """Resolve password cells from Excel (handles numeric values like ``12345``)."""
    if value is None or cell_text(value) == "":
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    return cell_text(value)


OTP_LENGTH = 6


def otp_is_complete(otp: str | None, *, length: int = OTP_LENGTH) -> bool:
    """Return whether ``otp`` has the full number of digits expected by Clerk."""
    if not otp:
        return False
    return len(otp) >= length


def term_accepted(case: TestRow) -> bool:
    """Return whether the legal checkbox should be checked (``term`` column: 1=yes, 0=no)."""
    term = case.get("term")
    if term is None:
        return False
    if isinstance(term, bool):
        return term
    if isinstance(term, (int, float)):
        return term != 0
    return cell_text(term) not in ("0", "false", "no", "")


def _random_suffix(length: int = 6) -> str:
    return "".join(secrets.choice(_RANDOM_SUFFIX_ALPHABET) for _ in range(length))


def uniquify_clerk_test_email(email: str, *, suffix_length: int = 6) -> str:
    """Turn ``name+clerk_test@domain`` into ``name<random>+clerk_test@domain``."""
    match = _CLERK_TEST_EMAIL.fullmatch(email.strip())
    if match is None:
        return email
    name = match.group("name")
    domain = match.group("domain")
    local = f"{name}{_random_suffix(suffix_length)}+clerk_test"
    return f"{local}@{domain}" if domain else local


def should_uniquify_sign_up_email(case: TestRow, email: str) -> bool:
    """Only mutate emails that match the clerk_test template and are meant to be valid."""
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
    """Resolve the sign-up email from Excel, uniquified when the case needs a fresh address."""
    raw = cell_value(case.get("email"))
    if raw is None:
        return None
    if should_uniquify_sign_up_email(case, raw):
        return uniquify_clerk_test_email(raw)
    return raw


def sign_up_assert_messages(case: TestRow) -> list[str]:
    """Messages that may appear for a sign-up row (primary + known Clerk/HTML5 variants)."""
    message = cell_text(case.get("message"))
    if not message:
        return []

    messages = [message]
    email = cell_value(case.get("email"))
    local = email.split("@", 1)[0] if email else ""

    if " " in local and "valid email" in message.lower():
        return ["Please fill out this field", message]

    return messages


def case_id(prefix: str, index: int, case: TestRow) -> str:
    message = cell_text(case.get("message"))
    if message:
        return f"{prefix}-{index + 1}-{message[:40]}"
    return f"{prefix}-{index + 1}-pass"


def message_lower(case: TestRow) -> str:
    return cell_text(case.get("message")).lower()


def sign_in_steps(case: TestRow) -> dict[str, bool]:
    """Decide how far the sign-in flow runs before asserting ``message``."""
    message = cell_text(case.get("message"))
    if not message:
        return {"email": True, "password": True, "otp": True}

    lower = message.lower()
    if "code" in lower:
        return {"email": True, "password": True, "otp": True}
    if "password" in lower:
        return {"email": True, "password": True, "otp": False}
    return {"email": True, "password": False, "otp": False}


def excel_flag(case: TestRow, column: str) -> bool | None:
    """Parse a 0/1 Excel flag column; ``None`` when the cell is empty."""
    value = case.get(column)
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return cell_text(value) not in ("0", "false", "no", "")


def log_out_all_devices(case: TestRow) -> bool | None:
    """Return whether the sign-out checkbox should be checked (``log_out``: 1=yes, 0=no)."""
    return excel_flag(case, "log_out")


def reset_password_steps(case: TestRow) -> dict[str, bool]:
    """Decide how far the reset-password flow runs before asserting ``message``.

    Uses the same step keys as ``sign_in_steps`` for the sign-in portion
    (``password`` = password page with forgot-password link, then OTP).
    """
    message = cell_text(case.get("message"))
    if not message:
        return {"email": True, "password": True, "otp": True, "reset": True}

    lower = message.lower()

    if "incorrect code" in lower or "enter code" in lower:
        return {"email": True, "password": True, "otp": True, "reset": False}

    return {"email": True, "password": True, "otp": True, "reset": True}


def reset_password_should_submit(case: TestRow) -> bool:
    """Return whether to click Reset Password (``submit``: 1=yes, 0=no)."""
    submit = excel_flag(case, "button")
    if submit is not None:
        return submit
    return True


def reset_password_assert_messages(case: TestRow) -> list[str]:
    """Messages that may appear for a reset-password row."""
    message = cell_text(case.get("message"))
    if not message:
        return []

    messages = [message]
    lower = message.lower()

    if "successfully changed" in lower:
        messages.append("Your password was successfully changed")
    if "not strong enough" in lower:
        messages.append("Your password is not strong enough")
    if "could be stronger" in lower:
        messages.append("Your password works, but could be stronger")

    return messages


def sign_up_steps(case: TestRow) -> dict[str, bool]:
    """Decide how far the sign-up flow runs before asserting ``message``."""
    message = cell_text(case.get("message"))
    email = cell_value(case.get("email"))
    password = cell_value(case.get("password"))
    legal = term_accepted(case)

    if not message:
        return {"email": True, "password": True, "legal": legal, "otp": True}

    lower = message.lower()

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


def assert_auth_outcome(
    page: AuthPage,
    driver: WebDriver,
    case: TestRow,
    *,
    field_for_assertion: Callable[[Any, TestRow], WebElement],
    auth_path: str,
    wait_timeout: float = 20,
    messages: list[str] | None = None,
) -> None:
    expected_messages = messages or [cell_text(case.get("message"))]
    expected_messages = [msg for msg in expected_messages if msg]

    if expected_messages:
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

    def _left_auth_flow(_: WebDriver) -> bool:
        url = driver.current_url
        return auth_path not in url and "factor-two" not in url

    WebDriverWait(driver, wait_timeout).until(_left_auth_flow)

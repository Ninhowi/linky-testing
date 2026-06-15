from __future__ import annotations

from cProfile import label
import re
import secrets
import string
from xml.parsers.expat import errors
from xml.parsers.expat import errors
from allure import label

import pytest
from selenium.webdriver.support.ui import WebDriverWait

from helpers.validation import assert_input_and_screen_message
from pages.sign_up import SignUpPage

pytestmark = pytest.mark.sign_up

_CLERK_EMAIL = re.compile(r"^(?P<name>.+?)\+clerk_test(?:@(?P<domain>.+))?$")
_CASES = [
    {"email": "linh+clerk_test@linky.now", "password": "ngoclinh1201@", "term": 0, "otp": "424242", "message": "Please check this box if you want to procced."},
    {"email": "ngoclinh+clerk_test", "password": "ngoclinh1201@", "term": 1, "otp": "424242", "message": "Please match the requested format"},
    {"email": None, "password": "ngoclinh1201@", "term": 1, "otp": "424242", "message": "Please fill out this field"},
    {"email": "linh+clerk_test@linky.now", "password": None, "term": 1, "otp": "424242", "message": "Please fill out this field"},
    {"email": "linh+clerk_test@linky.now", "password": "abc123", "term": 1, "otp": "424242", "message": "Your password must contain 8 or more characters."},
    {"email": "linh+clerk_test@linky.now", "password": "a" * 73, "term": 1, "otp": "424242", "message": "Your password must contain less than 72 characters."},
    {"email": "ngoclinh+clerk_test@linky.now", "password": "12Ngoclinh@", "term": 1, "otp": "424242", "message": "That email address is taken. Please try another."},
    {"email": "linh+clerk_test@linky.now", "password": "ngoclinh1201@", "term": 1, "otp": "123456", "message": "Incorrect code"},
    {"email": "linh+clerk_test@linky.now", "password": "ngoclinh1201@", "term": 1, "otp": None, "message": "Enter code"},
    {"email": "linh+clerk_test@linky.now", "password": "ngoclinh1201@", "term": 1, "otp": "12345", "message": "Enter code."},
    {"email": "lin h+clerk_test@linky.now", "password": "ngoclinh1201@", "term": 1, "otp": "424242", "message": "Email address must be a valid email address"},
    {"email": "linh+clerk_test@lin ky.now", "password": "ngoclinh1201@", "term": 1, "otp": "424242", "message": "Please match the requested format"},
    {"email": "linh+clerk_test@linky.now", "password": "ngoclinh1201@", "term": 1, "otp": "424242", "message": None},
]
def _txt(v: object) -> str:
     return "" if v is None else str(v)
def _unique(email: str) -> str:
    m = _CLERK_EMAIL.fullmatch(email.strip())
    if not m:
        return email
    sfx = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
    local = f"{m['name']}{sfx}+clerk_test"
    return f"{local}@{m['domain']}" if m.group("domain") else local
def _resolve_email(c: dict) -> str | None:
    raw = c.get("email")
    if raw is None:
        return None
    msg = _txt(c.get("message")).lower()
    if "+clerk_test" in raw and " " not in raw.split("@", 1)[0] and not any(
        p in msg for p in ("match the requested format", "valid email", "taken")
    ):
        return _unique(raw)
    return raw
def _steps(c: dict) -> tuple[bool, bool, bool, bool]:
    msg = _txt(c.get("message")).lower()
    legal = bool(c.get("term"))
    if not msg:
        return True, True, legal, True
    if "code" in msg:
        return True, True, legal, True
    if "check this box" in msg or "procced" in msg:
        return True, True, legal, False
    if "fill out this field" in msg:
        return c.get("email") is not None, c.get("password") is not None, legal, False
    if "password" in msg:
        return True, True, legal, False
    if any(p in msg for p in ("match the requested format", "valid email", "taken")):
        return True, True, legal, False
    return c.get("email") is not None, c.get("password") is not None, legal, False
def _messages(c: dict) -> list[str]:
    msg = _txt(c.get("message"))
    if not msg:
        return []
    email = _txt(c.get("email"))
    if " " in email.split("@", 1)[0] and "valid email" in msg.lower():
        return ["Please fill out this field", msg]
    return [msg]
def _field(page: SignUpPage, c: dict, steps: tuple[bool, bool, bool, bool]):
    msg = _txt(c.get("message")).lower()
    if "code" in msg or steps[3]:
        return page.otp.otp_input()
    if "password" in msg or (steps[1] and c.get("password") is not None):
        return page.form.password_input()
    if "check this box" in msg or "procced" in msg:
        return page.form.legal_input()
    return page.form.email_input()
def _run(page: SignUpPage, c: dict, steps: tuple[bool, bool, bool, bool]) -> None:
    use_email, use_password, legal, use_otp = steps
    page.form.fill(
        _resolve_email(c) if use_email else None,
        _txt(c.get("password")) if use_password and c.get("password") is not None else None,
        accept_legal=legal,
    )
    page.form.submit()
    if not use_otp:
        return
    page.otp.wait_until_visible()
    page.otp.clear_otp()
    otp = _txt(c.get("otp")) or None
    if otp:
        page.otp.fill_otp(otp)
    if not otp or len(otp) < 6:
        page.form.continue_button().click()
def _assert(page: SignUpPage, driver, c: dict, steps: tuple[bool, bool, bool, bool]) -> None:
    msgs = _messages(c)
    if msgs:
        field = lambda: _field(page, c, steps)
        errors: list[str] = []
        for msg in msgs:
            try:
                assert_input_and_screen_message(driver, field, msg)
                return
            except Exception as exc:
                errors.append(f"{msg!r}: {exc}")
        raise AssertionError("Expected message not found. Tried:\n" + "\n".join(errors))
    WebDriverWait(driver, 20).until(
        lambda d: "/sign-up" not in d.current_url and "factor-two" not in d.current_url
    )
def test_sign_up_all_cases_in_one(driver, base_url: str) -> None:
    errors: list[str] = []
    for i, case in enumerate(_CASES):
        label = f"signup-{i + 1}-{_txt(case.get('message'))[:40] or 'pass'}"
        try:
            page = SignUpPage.open(driver, base_url)
            steps = _steps(case)
            _run(page, case, steps)
            _assert(page, driver, case, steps)
        except Exception as exc:
            errors.append(f"{label}: {exc}")
    if errors:
        pytest.fail(
               f"{len(errors)}/{len(_CASES)} sign-up case(s) failed:\n" + "\n".join(errors),
            pytrace=False,
        )
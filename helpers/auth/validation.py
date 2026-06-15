"""HTML5 input validation helpers for Selenium.

Hàm hỗ trợ xác thực input HTML5 cho Selenium.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeAlias

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from helpers.browser.locators import assert_text_on_screen, text_xpath

InputRef: TypeAlias = WebElement | Callable[[], WebElement]

_POLL_INTERVAL_SEC = 0.2

_CLERK_FIELD_ERROR_SELECTORS = (
    "#error-emailAddress",
    "#error-password",
    "#error-newPassword",
    "#error-confirmPassword",
    "#error-legalAccepted",
    '[data-testid="form-feedback-error"]',
    ".cl-formFieldErrorText",
)

# One browser round-trip: reportValidity on target, then scan Clerk form controls.
_MATCH_VALIDATION_JS = """
const expected = arguments[1].toLowerCase().replace(/procced/g, 'proceed').trim();

function matches(actual) {
    const norm = (actual || '').toLowerCase().replace(/procced/g, 'proceed').trim();
    if (!norm) {
        return false;
    }
    return norm.includes(expected) || expected.includes(norm);
}

function read(el, report) {
    if (report) {
        el.reportValidity();
    }
    const invalid = !el.checkValidity();
    const msg = el.validationMessage || '';
    return { invalid, msg, matched: invalid && matches(msg) };
}

const target = arguments[0];
const targetState = read(target, true);
if (targetState.matched) {
    return targetState.msg;
}

const scope = document.querySelector('[data-clerk-ready="true"]') || document;
const form = scope.querySelector('form') || document.querySelector('form');
if (form) {
    form.reportValidity();
}

for (const el of scope.querySelectorAll('input, textarea')) {
    const invalid = !el.checkValidity();
    const msg = el.validationMessage || '';
    if (invalid && matches(msg)) {
        return msg;
    }
}

return null;
"""


def _normalize_message(text: str) -> str:
    return text.lower().replace("procced", "proceed").strip()


def _messages_match(expected: str, actual: str) -> bool:
    expected_norm = _normalize_message(expected)
    actual_norm = _normalize_message(actual)
    return expected_norm in actual_norm or actual_norm in expected_norm


def _clerk_field_error_visible(driver: WebDriver, message: str) -> bool:
    """Return whether a visible Clerk field error contains ``message``.

    Trả về lỗi trường Clerk hiển thị có chứa ``message`` hay không.
    """
    for selector in _CLERK_FIELD_ERROR_SELECTORS:
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                if not element.is_displayed():
                    continue
            except Exception:
                continue
            text = (element.text or "").strip()
            if text and _messages_match(message, text):
                return True
    return False


def _text_on_screen_visible(
    driver: WebDriver,
    message: str,
    *,
    exact: bool = False,
) -> bool:
    for element in driver.find_elements(By.XPATH, text_xpath(message, exact=exact)):
        try:
            if element.is_displayed():
                return True
        except Exception:
            continue
    return False


def _resolve_input(element: InputRef) -> WebElement | None:
    try:
        return element() if callable(element) else element
    except Exception:
        return None


def _validation_message_matches(
    driver: WebDriver,
    element: WebElement,
    message: str,
) -> bool:
    """Return True when ``message`` matches any relevant ``validationMessage``.

    Trả về True khi ``message`` khớp ``validationMessage`` liên quan.
    """
    matched = driver.execute_script(_MATCH_VALIDATION_JS, element, message)
    return matched is not None


def _auth_message_visible(
    driver: WebDriver,
    element: InputRef,
    message: str,
    *,
    exact: bool = False,
) -> bool:
    """Return whether ``message`` is visible via validation, Clerk errors, or screen text.

    Trả về ``message`` có hiển thị qua validation, lỗi Clerk hoặc văn bản màn hình.
    """
    input_el = _resolve_input(element)
    if input_el is not None:
        try:
            if _validation_message_matches(driver, input_el, message):
                return True
        except StaleElementReferenceException:
            pass

    if _clerk_field_error_visible(driver, message):
        return True

    return _text_on_screen_visible(driver, message, exact=exact)


def assert_input_and_screen_message(
    driver: WebDriver,
    element: InputRef,
    message: str,
    *,
    exact: bool = False,
    timeout: float = 10,
) -> None:
    """Assert ``message`` appears in ``validationMessage``, Clerk field errors, or on screen.

    Kiểm tra ``message`` xuất hiện trong ``validationMessage``, lỗi trường Clerk hoặc màn hình.
    """
    poll_timeout = max(timeout, 0.5)

    def _satisfied(_driver: WebDriver) -> bool:
        return _auth_message_visible(
            driver,
            element,
            message,
            exact=exact,
        )

    try:
        WebDriverWait(driver, poll_timeout, poll_frequency=_POLL_INTERVAL_SEC).until(
            _satisfied
        )
        return
    except TimeoutException:
        pass

    input_el = _resolve_input(element)
    if input_el is not None:
        try:
            if _validation_message_matches(driver, input_el, message):
                return
        except StaleElementReferenceException:
            pass

    if _clerk_field_error_visible(driver, message):
        return

    if _text_on_screen_visible(driver, message, exact=exact):
        return

    try:
        assert_text_on_screen(driver, message, exact=exact, timeout=0)
    except TimeoutException as exc:
        raise AssertionError(
            f"Expected {message!r} from validation, Clerk field error, or on screen"
        ) from exc

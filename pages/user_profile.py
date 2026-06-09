"""User profile page at ``/user/profile``."""

from __future__ import annotations

import re
import time

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from helpers.locators import wait_for_text
from helpers.validation import _messages_match
from helpers.waits import DEFAULT_TIMEOUT_SEC, wait_present
from pages.clerk_form import _SET_INPUT_VALUE_JS

_PROFILE_SECTIONS = ("profile-header", "bio", "personal", "interests")
_SAVE_WAIT_TIMEOUT_SEC = 15.0
_TOAST_AFTER_SAVE_SEC = 0.1
_TOAST_ASSERT_TIMEOUT_SEC = 2.0
_FIELD_ERROR_TIMEOUT_SEC = 5.0
_FIELD_ERROR_POLL_SEC = 0.05
_UI_SETTLE_SEC = 0.3
_FIELD_ERROR_SELECTOR = ".text-destructive"
_CHAR_COUNTER_PATTERN = re.compile(r"^\d+/\d+$")

_ARIA_FIELDS: dict[str, str] = {
    "first_name": "First name",
    "last_name": "Last name",
    "bio": "Bio",
    "date": "Select date",
}

_COMBOBOX_COLUMNS = frozenset({"country", "gender", "interest"})

_SETTLE_FIELD_JS = """
const element = arguments[0];
element.dispatchEvent(new Event('blur', { bubbles: true }));
element.dispatchEvent(new Event('change', { bubbles: true }));
"""


def _action_selector(section: str, action: str) -> str:
    return f'[name="{action}-{section}"]'


def _button_enabled(button: WebElement) -> bool:
    disabled = button.get_attribute("disabled")
    aria_disabled = button.get_attribute("aria-disabled")
    if disabled is not None or aria_disabled == "true":
        return False
    return button.is_enabled()


def _button_label(button: WebElement) -> str:
    return (button.text or "").strip().lower()


def _save_showing_done(button: WebElement) -> bool:
    return _button_label(button) == "done"


def _is_inline_field_error(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    return not _CHAR_COUNTER_PATTERN.match(stripped)


def _click(driver: WebDriver, element: WebElement) -> None:
    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
        element,
    )
    time.sleep(_UI_SETTLE_SEC)


class ProfileSection:
    def __init__(self, driver: WebDriver, name: str) -> None:
        self._driver = driver
        self._name = name

    @property
    def root(self) -> WebElement:
        elements = self._driver.find_elements(
            By.CSS_SELECTOR,
            f'div[class*="group/{self._name}"]',
        )
        if elements:
            return elements[0]
        for action in ("save", "edit", "cancel"):
            try:
                button = self._find_action_button(action)
            except TimeoutException:
                continue
            return button.find_element(
                By.XPATH,
                "./ancestor::div[contains(@class, 'group/')][1]",
            )
        raise TimeoutException(f"No root found for profile section {self._name!r}")

    def _find_action_button(self, action: str) -> WebElement:
        elements = self._driver.find_elements(
            By.CSS_SELECTOR,
            _action_selector(self._name, action),
        )
        if elements:
            return elements[0]
        raise TimeoutException(
            f"No {action!r} button found for profile section {self._name!r}"
        )

    def edit_button(self) -> WebElement:
        return self._find_action_button("edit")

    def save_button(self) -> WebElement:
        return self._find_action_button("save")

    def cancel_button(self) -> WebElement:
        return self._find_action_button("cancel")

    def _section_roots(self) -> list[WebElement]:
        roots = self._driver.find_elements(
            By.CSS_SELECTOR,
            f'div[class*="group/{self._name}"]',
        )
        return roots

    def field_anchor(self, column: str) -> WebElement:
        """Return the input or combobox trigger for ``column``."""
        if column in _ARIA_FIELDS:
            label = _ARIA_FIELDS[column]
            selector = f"input[aria-label='{label}'], textarea[aria-label='{label}']"
            for element in self._driver.find_elements(By.CSS_SELECTOR, selector):
                if element.is_displayed():
                    return element
            raise TimeoutException(f"No visible field with aria-label {label!r}")

        if column in _COMBOBOX_COLUMNS:
            return self._combobox_trigger(column)
        raise ValueError(f"Unsupported profile column {column!r}")

    def all_field_errors(self) -> list[str]:
        """Return visible inline error messages within this section."""
        texts: list[str] = []
        scopes = self._section_roots() or [self._driver.find_element(By.TAG_NAME, "body")]
        for scope in scopes:
            for element in scope.find_elements(By.CSS_SELECTOR, _FIELD_ERROR_SELECTOR):
                try:
                    if not element.is_displayed():
                        continue
                except StaleElementReferenceException:
                    continue
                text = (element.text or "").strip()
                if _is_inline_field_error(text):
                    texts.append(text)
        return texts

    def field_error_text(self, column: str) -> str | None:
        """Return visible inline error text beside ``column``, if any."""
        try:
            anchor = self.field_anchor(column)
        except (TimeoutException, StaleElementReferenceException):
            return self._first_matching_field_error(
                self.all_field_errors(),
                column=column,
            )

        for xpath in (
            "./ancestor::div[contains(@class, 'space-y')][1]",
            "./parent::*",
        ):
            try:
                container = anchor.find_element(By.XPATH, xpath)
            except Exception:
                continue
            for element in container.find_elements(By.CSS_SELECTOR, _FIELD_ERROR_SELECTOR):
                try:
                    if not element.is_displayed():
                        continue
                except StaleElementReferenceException:
                    continue
                text = (element.text or "").strip()
                if _is_inline_field_error(text):
                    return text

        return self._first_matching_field_error(self.all_field_errors(), column=column)

    @staticmethod
    def _first_matching_field_error(
        errors: list[str],
        *,
        column: str,
    ) -> str | None:
        if not errors:
            return None
        if len(errors) == 1:
            return errors[0]
        column_hints = {
            "first_name": ("first name",),
            "last_name": ("last name",),
            "date": ("date", "birth"),
            "interest": ("tag",),
            "bio": ("bio", "300", "character"),
        }
        hints = column_hints.get(column, ())
        for text in errors:
            lower = text.lower()
            if any(hint in lower for hint in hints) and any(
                word in lower for word in ("must", "cannot", "invalid", "should")
            ):
                return text
        for text in errors:
            lower = text.lower()
            if any(hint in lower for hint in hints):
                return text
        return errors[0]

    def _aria_input(self, label: str) -> WebElement:
        selector = f"input[aria-label='{label}'], textarea[aria-label='{label}']"
        for element in self.root.find_elements(By.CSS_SELECTOR, selector):
            if element.is_displayed():
                return element
        for element in self._driver.find_elements(By.CSS_SELECTOR, selector):
            if element.is_displayed():
                return element
        raise TimeoutException(f"No field with aria-label {label!r}")

    def _combobox_trigger(self, column: str) -> WebElement:
        root = self.root
        action_names = {
            f"edit-{self._name}",
            f"save-{self._name}",
            f"cancel-{self._name}",
        }
        hints = {
            "country": ("vietnam", "country"),
            "gender": ("male", "female", "gender"),
            "interest": ("select a tag", "tag"),
        }
        hint_terms = hints[column]

        for button in root.find_elements(By.TAG_NAME, "button"):
            try:
                if not button.is_displayed():
                    continue
            except StaleElementReferenceException:
                continue
            name = button.get_attribute("name") or ""
            if name in action_names:
                continue
            try:
                text = (button.text or "").lower()
            except StaleElementReferenceException:
                continue
            if column == "interest" and "select a tag" in text:
                return button
            if any(term in text for term in hint_terms):
                return button

        raise TimeoutException(f"No combobox trigger for {column!r} in {self._name!r}")

    def _cmdk_search_input(self, *, placeholder_hint: str) -> WebElement:
        for element in self._driver.find_elements(By.CSS_SELECTOR, "input[cmdk-input]"):
            if element.is_displayed():
                return element
        for element in self._driver.find_elements(By.CSS_SELECTOR, "input"):
            placeholder = (element.get_attribute("placeholder") or "").lower()
            if element.is_displayed() and placeholder_hint in placeholder:
                return element
        raise TimeoutException(f"No cmdk search input for {placeholder_hint!r}")

    def _click_listbox_option(self, value: str) -> None:
        value_lower = value.strip().lower()
        for selector in ("[role='option']", "[cmdk-item]"):
            for option in self._driver.find_elements(By.CSS_SELECTOR, selector):
                try:
                    if not option.is_displayed():
                        continue
                except StaleElementReferenceException:
                    continue
                text = (option.text or option.get_attribute("textContent") or "").strip()
                if text.lower() == value_lower or value_lower in text.lower():
                    _click(self._driver, option)
                    return

    def _settle_field(self, field: WebElement) -> None:
        self._driver.execute_script(_SETTLE_FIELD_JS, field)
        time.sleep(_UI_SETTLE_SEC)

    def _fill_input_value(self, field: WebElement, value: str) -> None:
        self._driver.execute_script("arguments[0].focus();", field)
        field.clear()
        if (
            not value
            or len(value) > 100
            or any(ord(ch) > 0xFFFF for ch in value)
            or "\n" in value
        ):
            self._driver.execute_script(_SET_INPUT_VALUE_JS, field, value)
        else:
            field.send_keys(value)
        self._settle_field(field)

    def _ensure_input_value(self, field: WebElement, value: str) -> None:
        self._fill_input_value(field, value)
        for attempt in range(3):
            actual = field.get_attribute("value") or ""
            if actual == value:
                return
            if attempt == 1 and len(value) > 100:
                field.clear()
                for offset in range(0, len(value), 50):
                    field.send_keys(value[offset : offset + 50])
                self._settle_field(field)
                continue
            self._fill_input_value(field, value)

        actual = field.get_attribute("value") or ""
        raise AssertionError(
            f"Could not set field value (expected len {len(value)}, got {len(actual)})"
        )

    def fill_text(self, column: str, value: str) -> None:
        if column in _ARIA_FIELDS:
            inp = self._aria_input(_ARIA_FIELDS[column])
            self._ensure_input_value(inp, value)
            return

        if column not in _COMBOBOX_COLUMNS:
            raise ValueError(f"Unsupported profile column {column!r}")

        trigger = self._combobox_trigger(column)
        _click(self._driver, trigger)

        if column == "country":
            search = self._cmdk_search_input(placeholder_hint="search country")
            search.clear()
            search.send_keys(value.strip())
            time.sleep(_UI_SETTLE_SEC)
            self._click_listbox_option(value)
            return

        if column == "gender":
            self._click_listbox_option(value)
            return

        if column == "interest":
            search = self._cmdk_search_input(placeholder_hint="search")
            search.clear()
            search.send_keys(value)
            time.sleep(_UI_SETTLE_SEC)
            try:
                self._click_listbox_option(value)
            except Exception:
                pass
            return


class UserProfilePage:
    PATH = "/user/profile"
    TOAST_AFTER_SAVE_SEC = _TOAST_AFTER_SAVE_SEC

    def __init__(self, driver: WebDriver) -> None:
        self._driver = driver

    @classmethod
    def open(cls, driver: WebDriver, base_url: str) -> UserProfilePage:
        driver.get(f"{base_url.rstrip('/')}{cls.PATH}")
        cls.wait_until_ready(driver)
        return cls(driver)

    @classmethod
    def wait_until_ready(cls, driver: WebDriver, timeout: float | None = None) -> None:
        t = timeout or DEFAULT_TIMEOUT_SEC
        for section in _PROFILE_SECTIONS:
            locator = (By.CSS_SELECTOR, _action_selector(section, "edit"))
            try:
                wait_present(driver, locator, t)
            except TimeoutException as exc:
                raise TimeoutException(
                    f"Profile section {section!r} did not become ready"
                ) from exc

    def section(self, name: str) -> ProfileSection:
        return ProfileSection(self._driver, name)

    def edit_section(self, name: str) -> None:
        _click(self._driver, self.section(name).edit_button())

    def click_save_section(self, name: str) -> None:
        section = self.section(name)
        WebDriverWait(self._driver, _SAVE_WAIT_TIMEOUT_SEC).until(
            lambda _: _button_enabled(section.save_button())
        )
        save_btn = section.save_button()
        _click(self._driver, save_btn)

    def wait_save_section(self, name: str, *, stop_on_field_error: bool = False) -> None:
        section = self.section(name)

        def _save_in_progress(_: WebDriver) -> bool:
            try:
                save_btn = section.save_button()
            except (NoSuchElementException, StaleElementReferenceException):
                return True
            if _save_showing_done(save_btn):
                return True
            return not _button_enabled(save_btn)

        try:
            WebDriverWait(self._driver, 2.0, poll_frequency=0.05).until(_save_in_progress)
        except TimeoutException:
            pass

        def _save_finished(_: WebDriver) -> bool:
            if stop_on_field_error and section.all_field_errors():
                return True
            buttons = self._driver.find_elements(
                By.CSS_SELECTOR,
                _action_selector(name, "save"),
            )
            if not buttons:
                return True
            save_btn = buttons[0]
            if _save_showing_done(save_btn):
                return True
            return _button_enabled(save_btn)

        WebDriverWait(self._driver, _SAVE_WAIT_TIMEOUT_SEC, poll_frequency=0.05).until(
            _save_finished
        )

    def save_section(self, name: str) -> None:
        self.click_save_section(name)
        self.wait_save_section(name)

    def fill_fields(self, section_name: str, fields: list[tuple[str, str]]) -> None:
        section = self.section(section_name)
        for column, value in fields:
            section.fill_text(column, value)

    def assert_field_error(
        self,
        section_name: str,
        column: str,
        messages: str | list[str],
        *,
        timeout: float = _FIELD_ERROR_TIMEOUT_SEC,
    ) -> None:
        expected = [messages] if isinstance(messages, str) else messages
        section = self.section(section_name)

        def _field_error_visible(_: WebDriver) -> bool:
            try:
                text = section.field_error_text(column)
            except StaleElementReferenceException:
                return False
            if text and any(_messages_match(message, text) for message in expected):
                return True
            return any(
                _messages_match(message, error)
                for message in expected
                for error in section.all_field_errors()
            )

        try:
            WebDriverWait(self._driver, timeout, poll_frequency=_FIELD_ERROR_POLL_SEC).until(
                _field_error_visible
            )
        except TimeoutException as exc:
            try:
                actual = section.field_error_text(column)
                all_errors = section.all_field_errors()
            except StaleElementReferenceException:
                actual = None
                all_errors = []
            raise AssertionError(
                f"Expected field error near {column!r} in section {section_name!r}. "
                f"Tried: {expected!r}; actual: {actual!r}; section errors: {all_errors!r}"
            ) from exc

    def assert_toast(
        self,
        messages: str | list[str],
        *,
        timeout: float = _TOAST_ASSERT_TIMEOUT_SEC,
    ) -> None:
        expected = [messages] if isinstance(messages, str) else [msg for msg in messages if msg]
        if not expected:
            return

        time.sleep(_TOAST_AFTER_SAVE_SEC)
        errors: list[str] = []
        for message in expected:
            try:
                wait_for_text(self._driver, message, timeout=timeout)
                return
            except TimeoutException as exc:
                errors.append(f"{message!r}: {exc}")
        raise AssertionError(
            "Expected toast message not found. Tried:\n" + "\n".join(errors)
        )

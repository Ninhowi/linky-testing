"""User profile page at ``/user/profile``."""

from __future__ import annotations

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
from helpers.waits import DEFAULT_TIMEOUT_SEC, wait_present
from pages.clerk_form import _SET_INPUT_VALUE_JS

_PROFILE_SECTIONS = ("profile-header", "bio", "personal", "interests")
_SAVE_WAIT_TIMEOUT_SEC = 15.0
_TOAST_AFTER_SAVE_SEC = 0.1
_TOAST_ASSERT_TIMEOUT_SEC = 2.0
_UI_SETTLE_SEC = 0.3

_ARIA_FIELDS: dict[str, str] = {
    "first_name": "First name",
    "last_name": "Last name",
    "bio": "Bio",
    "date": "Select date",
}

_COMBOBOX_COLUMNS = frozenset({"country", "gender", "interest"})


def _attr_selector(attr: str, value: str) -> str:
    return f'[{attr}="{value}"]'


def _action_selector(section: str, action: str, *, attr: str = "name") -> str:
    return _attr_selector(attr, f"{action}-{section}")


def _button_enabled(button: WebElement) -> bool:
    disabled = button.get_attribute("disabled")
    aria_disabled = button.get_attribute("aria-disabled")
    if disabled is not None or aria_disabled == "true":
        return False
    return button.is_enabled()


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
        for selector in (
            _attr_selector("data-name", self._name),
            f'div[class*="group/{self._name}"]',
        ):
            elements = self._driver.find_elements(By.CSS_SELECTOR, selector)
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
        for attr in ("data-name", "name"):
            selector = _action_selector(self._name, action, attr=attr)
            elements = self._driver.find_elements(By.CSS_SELECTOR, selector)
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
            if not button.is_displayed():
                continue
            name = button.get_attribute("name") or ""
            if name in action_names:
                continue
            text = (button.text or "").lower()
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

    def fill_text(self, column: str, value: str) -> None:
        if column in _ARIA_FIELDS:
            inp = self._aria_input(_ARIA_FIELDS[column])
            inp.clear()
            if any(ord(ch) > 0xFFFF for ch in value) or "\n" in value:
                self._driver.execute_script(_SET_INPUT_VALUE_JS, inp, value)
            else:
                inp.send_keys(value)
            time.sleep(_UI_SETTLE_SEC)
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
            found = False
            for attr in ("data-name", "name"):
                locator = (By.CSS_SELECTOR, _action_selector(section, "edit", attr=attr))
                try:
                    wait_present(driver, locator, t)
                    found = True
                    break
                except TimeoutException:
                    continue
            if not found:
                raise TimeoutException(
                    f"Profile section {section!r} did not become ready"
                )

    def section(self, name: str) -> ProfileSection:
        return ProfileSection(self._driver, name)

    def edit_section(self, name: str) -> None:
        _click(self._driver, self.section(name).edit_button())

    def save_section(self, name: str) -> None:
        section = self.section(name)
        save_btn = section.save_button()
        if not _button_enabled(save_btn):
            WebDriverWait(self._driver, _SAVE_WAIT_TIMEOUT_SEC).until(
                lambda _: _button_enabled(section.save_button())
            )
            save_btn = section.save_button()

        _click(self._driver, save_btn)

        def _became_disabled(_: WebDriver) -> bool:
            try:
                return not _button_enabled(section.save_button())
            except (NoSuchElementException, StaleElementReferenceException):
                return True

        try:
            WebDriverWait(self._driver, 2.0, poll_frequency=0.05).until(_became_disabled)
        except TimeoutException:
            pass

        def _save_finished(_: WebDriver) -> bool:
            for attr in ("data-name", "name"):
                buttons = self._driver.find_elements(
                    By.CSS_SELECTOR,
                    _action_selector(name, "save", attr=attr),
                )
                if not buttons:
                    return True
                if _button_enabled(buttons[0]):
                    return True
            return False

        WebDriverWait(self._driver, _SAVE_WAIT_TIMEOUT_SEC, poll_frequency=0.05).until(
            _save_finished
        )

    def fill_fields(self, section_name: str, fields: list[tuple[str, str]]) -> None:
        section = self.section(section_name)
        for column, value in fields:
            section.fill_text(column, value)

    def assert_toast(self, message: str, *, timeout: float = _TOAST_ASSERT_TIMEOUT_SEC) -> None:
        time.sleep(_TOAST_AFTER_SAVE_SEC)
        try:
            wait_for_text(self._driver, message, timeout=timeout)
        except TimeoutException as exc:
            raise AssertionError(f"Expected toast message {message!r}") from exc

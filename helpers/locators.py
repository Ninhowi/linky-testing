"""Selenium locators and assertions for visible text on screen."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import re
from typing import Pattern

_INPUT_ATTRS = ("aria-label", "name", "id", "placeholder", "autocomplete")

def _input_label_text(el: WebElement) -> str:
    parts = [el.text or ""]
    for attr in _INPUT_ATTRS:
        val = el.get_attribute(attr)
        if val:
            parts.append(val)
    return "\n".join(parts)

def _input_matches_name(el: WebElement, name: str | Pattern[str]) -> bool:
    haystack = _input_label_text(el)
    if isinstance(name, Pattern):
        return bool(name.search(haystack))
    return name.lower() in haystack.lower()

def _find_input_by_name(driver: WebDriver, name: str | Pattern[str]) -> WebElement:
    xpath = (
        "//input[(@type='text' or @type='email' or @type='password' or not(@type)) "
        "and not(@type='hidden')]"
    )
    label = name.pattern if isinstance(name, Pattern) else name
    for el in driver.find_elements(By.XPATH, xpath):
        if el.is_displayed() and _input_matches_name(el, name):
            return el
    raise Exception(f"No element role=textbox name~={label}")

def by_role(
    driver: WebDriver,
    role: str,
    *,
    name: str | Pattern[str] | None = None,
) -> WebElement:
    if role == "button":
        tag = "button"
    elif role == "textbox":
        tag = "input"
    elif role == "link":
        tag = "a"
    else:
        tag = "*"

    if name is None:
        return driver.find_element(By.TAG_NAME, tag) if tag != "*" else driver.find_element(By.XPATH, "//*")

    if tag == "input":
        return _find_input_by_name(driver, name)

    if isinstance(name, Pattern):
        pattern = name.pattern
        xpath = (
            f"//{tag}[contains(translate(normalize-space(.), "
            f"'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), "
            f"'{pattern.lower()}')]"
        )
        elements = driver.find_elements(By.XPATH, xpath)
        for el in elements:
            if name.search(el.text or el.get_attribute("aria-label") or ""):
                return el
        raise Exception(f"No element role={role} name~={pattern}")

    name_lower = name.lower()
    if tag == "button":
        xpath = (
            f"//button[contains(translate(normalize-space(.), "
            f"'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name_lower}')]"
        )
    elif tag == "a":
        xpath = (
            f"//a[contains(translate(normalize-space(.), "
            f"'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name_lower}')]"
        )
    else:
        xpath = f"//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name_lower}')]"
    return driver.find_element(By.XPATH, xpath)

def scoped_css(scope: str, selectors: str) -> str:
    return ", ".join(f"{scope}{part.strip()}" for part in selectors.split(","))

def first_visible_css(driver: WebDriver, *selector_groups: str) -> WebElement | None:
    for group in selector_groups:
        for el in driver.find_elements(By.CSS_SELECTOR, group):
            if el.is_displayed():
                return el
    return None

def _xpath_literal(text: str) -> str:
    if "'" not in text:
        return f"'{text}'"
    if '"' not in text:
        return f'"{text}"'
    parts = text.split("'")
    return "concat(" + ", \"'\", ".join(f"'{part}'" for part in parts) + ")"


def text_xpath(text: str, *, exact: bool = False) -> str:
    """Build an XPath that matches an element containing ``text``."""
    literal = _xpath_literal(text)
    if exact:
        return f"//*[normalize-space(.)={literal}]"
    return f"//*[contains(normalize-space(.), {literal})]"


def wait_for_text(
    driver: WebDriver,
    text: str,
    *,
    exact: bool = False,
    timeout: float = 10,
) -> WebElement:
    """Wait until ``text`` is visible and return the matching element."""
    locator = (By.XPATH, text_xpath(text, exact=exact))
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located(locator)
    )


def assert_text_on_screen(
    driver: WebDriver,
    text: str,
    *,
    exact: bool = False,
    timeout: float = 10,
) -> WebElement:
    """Assert that ``text`` is visible on screen."""
    return wait_for_text(driver, text, exact=exact, timeout=timeout)

"""User profile page CSS selectors and selector builders.

Selector CSS và hàm tạo selector cho trang hồ sơ người dùng.
"""

from __future__ import annotations

_FIELD_ERROR_SELECTOR = ".text-destructive"
_COMBOBOX_EMPTY_SELECTORS = ("[cmdk-empty]", "[data-slot='command-empty']")
_COMBOBOX_POPOVER_SELECTOR = "[data-radix-popper-content-wrapper]"
_COMBOBOX_CLOSE_SELECTORS = (
    "[data-radix-popper-content-wrapper]",
    "[cmdk-root]",
    "[role='listbox']",
)
_COMBOBOX_OPTION_SELECTORS = ("[role='option']", "[cmdk-item]")
_COMBOBOX_INPUT_SELECTOR = "input[cmdk-input]"
_COMBOBOX_POPOVER_INPUT_SELECTOR = "input[cmdk-input], input"

_ARIA_FIELDS: dict[str, str] = {
    "first_name": "First name",
    "last_name": "Last name",
    "bio": "Bio",
    "date": "Select date",
}

_SECTION_ANCESTOR_XPATH = "./ancestor::div[contains(@class, 'group/')][1]"
_FIELD_ERROR_CONTAINER_XPATH = "./ancestor::div[contains(@class, 'space-y')][1]"


def action_selector(section: str, action: str) -> str:
    return f'[name="{action}-{section}"]'


def section_root_selector(section: str) -> str:
    return f'div[class*="group/{section}"]'


def aria_field_selector(label: str) -> str:
    return f"input[aria-label='{label}'], textarea[aria-label='{label}']"

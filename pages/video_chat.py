"""Video chat page object model."""

from __future__ import annotations

from re
from time

from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from helpers.locators import wait_for_text
from helpers.validation import _messages_match
from helpers.waits import DEFAULT_TIMEOUT_SEC, wait_present
from pages.clerk_form import _SET_INPUT_VALUE_JS
from pages.selectors.video_chat import _VIDEO_CHAT_IDLE_STATE

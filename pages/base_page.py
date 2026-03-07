"""Base page with shared driver, wait, and URL."""
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    """Base class for all page objects. Holds driver and wait instances."""

    BASE_URL = "https://www.linkynow.site"

    def __init__(self, driver: WebDriver, wait: WebDriverWait, wait_auth: WebDriverWait):
        self.driver = driver
        self.wait = wait
        self.wait_auth = wait_auth

    def open(self, path: str) -> None:
        """Navigate to BASE_URL + path."""
        self.driver.get(f"{self.BASE_URL}{path}")

    @property
    def current_url(self) -> str:
        return self.driver.current_url

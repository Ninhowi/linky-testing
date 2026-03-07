"""Pytest fixtures for POM tests: driver, waits, page objects."""
import pytest
from selenium.webdriver.support.ui import WebDriverWait

from utils.chrome_driver import custom_chrome_driver
from utils.configure import isEnableHeadless
from pages.sign_up_page import SignUpPage
from pages.sign_in_page import SignInPage
from pages.verify_email_page import VerifyEmailPage
from pages.dashboard_page import DashboardPage


@pytest.fixture(scope="function")
def driver():
    """One Chrome driver per test."""
    d = custom_chrome_driver(enable_headless=isEnableHeadless())
    d.implicitly_wait(0)
    yield d
    d.quit()


@pytest.fixture
def wait(driver):
    return WebDriverWait(driver, 5, poll_frequency=0.2)


@pytest.fixture
def wait_auth(driver):
    return WebDriverWait(driver, 10, poll_frequency=0.2)


@pytest.fixture
def sign_up_page(driver, wait, wait_auth):
    return SignUpPage(driver, wait, wait_auth)


@pytest.fixture
def sign_in_page(driver, wait, wait_auth):
    return SignInPage(driver, wait, wait_auth)


@pytest.fixture
def verify_email_page(driver, wait, wait_auth):
    return VerifyEmailPage(driver, wait, wait_auth)


@pytest.fixture
def dashboard_page(driver, wait, wait_auth):
    return DashboardPage(driver, wait, wait_auth)

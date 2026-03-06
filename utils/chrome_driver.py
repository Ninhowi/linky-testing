"""Chrome WebDriver setup (managed via webdriver-manager)."""
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

def custom_chrome_driver(enable_headless=False):
    options = Options()
    if enable_headless:
        options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_experimental_option("detach", True)

    service = ChromeService(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    return driver
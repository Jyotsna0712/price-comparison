from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class BrowserConfig:
    headless: bool = True
    page_load_timeout: int = 15
    implicit_wait_seconds: int = 2


def make_chrome_driver(*, headless: bool = True, page_load_timeout: int = 15):
    """
    Create a headless Chrome webdriver.

    If Selenium/driver dependencies are missing, this returns None so callers
    can fall back to requests-based scraping.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
    except Exception:
        return None

    try:
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1400,900")
        # Helps with some bot detection.
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
        )

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(page_load_timeout)
        driver.implicitly_wait(2)
        return driver
    except Exception:
        # Driver installation/launch is often blocked by network policies.
        # In that case we fall back to requests-based scraping.
        return None


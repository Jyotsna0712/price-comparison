from __future__ import annotations

from dataclasses import dataclass
from typing import List

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

from .browser import make_chrome_driver

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class ProductResult:
    title: str
    price: float | None
    rating: str | None
    product_url: str
    image_url: str
    source: str = "Amazon"

    @property
    def price_display(self) -> str:
        if self.price is None:
            return "Price unavailable"
        return f"₹{self.price:,.2f}"


def parse_price(text: str | None) -> float | None:
    if not text:
        return None
    digits = "".join(ch for ch in text if ch.isdigit() or ch == ".")
    try:
        return float(digits)
    except ValueError:
        return None


def search_amazon(query: str, timeout: int = 8) -> List[ProductResult]:
    """
    Perform a simple scrape of Amazon search results.

    This is intentionally defensive: if Amazon layout or access changes,
    we return an empty list instead of raising.
    """
    url = "https://www.amazon.in/s"
    params = {"k": query}

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
    except Exception:
        resp = None

    if resp is not None:
        soup = BeautifulSoup(resp.text, "html.parser")
        results: List[ProductResult] = []

        for card in soup.select(
            "div.s-result-item[data-component-type='s-search-result']"
        )[:10]:
            # Title
            title_el = card.select_one("h2 a span")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)

            # URL
            link_el = card.select_one("h2 a")
            href = link_el.get("href") if link_el else ""
            product_url = (
                f"https://www.amazon.in{href}"
                if href and href.startswith("/")
                else href
            )

            # Image
            img_el = card.select_one("img.s-image")
            image_url = img_el.get("src") if img_el else ""

            # Price
            price_el = card.select_one("span.a-price span.a-offscreen")
            price_text = price_el.get_text(strip=True) if price_el else None
            price = parse_price(price_text)

            # Rating
            rating_el = card.select_one("span.a-icon-alt")
            rating = rating_el.get_text(strip=True) if rating_el else None

            results.append(
                ProductResult(
                    title=title,
                    price=price,
                    rating=rating,
                    product_url=product_url,
                    image_url=image_url,
                )
            )

        if results:
            return results

    # Fallback to Selenium for layouts protected by anti-bot / JS rendering.
    driver = make_chrome_driver(headless=True, page_load_timeout=timeout + 7)
    if driver is None:
        return []

    try:
        wait_url = f"https://www.amazon.in/s?k={quote_plus(query)}"
        driver.get(wait_url)

        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.support.ui import WebDriverWait

            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "div.s-result-item[data-component-type='s-search-result']",
                    )
                )
            )
        except Exception:
            # Even if wait fails, attempt parsing what we have.
            pass

        soup = BeautifulSoup(driver.page_source, "html.parser")
        results = []

        for card in soup.select(
            "div.s-result-item[data-component-type='s-search-result']"
        )[:10]:
            title_el = card.select_one("h2 a span")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)

            link_el = card.select_one("h2 a")
            href = link_el.get("href") if link_el else ""
            product_url = (
                f"https://www.amazon.in{href}"
                if href and href.startswith("/")
                else href
            )

            img_el = card.select_one("img.s-image")
            image_url = img_el.get("src") if img_el else ""

            price_el = card.select_one("span.a-price span.a-offscreen")
            price_text = price_el.get_text(strip=True) if price_el else None
            price = parse_price(price_text)

            rating_el = card.select_one("span.a-icon-alt")
            rating = rating_el.get_text(strip=True) if rating_el else None

            results.append(
                ProductResult(
                    title=title,
                    price=price,
                    rating=rating,
                    product_url=product_url,
                    image_url=image_url,
                )
            )

        return results
    except Exception:
        # Any Selenium/driver runtime failure should not break the app.
        return []
    finally:
        try:
            driver.quit()
        except Exception:
            pass


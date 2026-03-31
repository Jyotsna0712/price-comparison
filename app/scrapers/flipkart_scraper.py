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
}


@dataclass
class ProductResult:
    title: str
    price: float | None
    rating: str | None
    product_url: str
    image_url: str
    source: str = "Flipkart"

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


def search_flipkart(query: str, timeout: int = 8) -> List[ProductResult]:
    """
    Perform a simple scrape of Flipkart search results.
    """
    url = "https://www.flipkart.com/search"
    params = {"q": query}

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
    except Exception:
        resp = None

    if resp is not None:
        soup = BeautifulSoup(resp.text, "html.parser")
        results: List[ProductResult] = []

        # Flipkart has different card layouts; handle a couple of common ones.
        for card in soup.select("div._1AtVbE")[:10]:
            title_el = card.select_one("div._4rR01T") or card.select_one("a.s1Q9rs")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)

            # URL
            link_el = card.select_one("a._1fQZEK") or card.select_one("a.s1Q9rs")
            href = link_el.get("href") if link_el else ""
            product_url = (
                f"https://www.flipkart.com{href}"
                if href and href.startswith("/")
                else href
            )

            # Image
            img_el = card.select_one("img._396cs4") or card.select_one("img._2r_T1I")
            image_url = img_el.get("src") if img_el else ""

            # Price
            price_el = card.select_one("div._30jeq3._1_WHN1") or card.select_one("div._30jeq3")
            price_text = price_el.get_text(strip=True) if price_el else None
            price = parse_price(price_text)

            # Rating
            rating_el = card.select_one("div._3LWZlK")
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

    # Fallback to Selenium for JS-rendered / protected pages.
    driver = make_chrome_driver(headless=True, page_load_timeout=timeout + 7)
    if driver is None:
        return []

    try:
        wait_url = f"https://www.flipkart.com/search?q={quote_plus(query)}"
        driver.get(wait_url)

        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.support.ui import WebDriverWait

            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div._1AtVbE"))
            )
        except Exception:
            pass

        soup = BeautifulSoup(driver.page_source, "html.parser")
        results: List[ProductResult] = []

        for card in soup.select("div._1AtVbE")[:10]:
            title_el = card.select_one("div._4rR01T") or card.select_one("a.s1Q9rs")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)

            link_el = card.select_one("a._1fQZEK") or card.select_one("a.s1Q9rs")
            href = link_el.get("href") if link_el else ""
            product_url = (
                f"https://www.flipkart.com{href}"
                if href and href.startswith("/")
                else href
            )

            img_el = card.select_one("img._396cs4") or card.select_one("img._2r_T1I")
            image_url = img_el.get("src") if img_el else ""

            price_el = card.select_one("div._30jeq3._1_WHN1") or card.select_one("div._30jeq3")
            price_text = price_el.get_text(strip=True) if price_el else None
            price = parse_price(price_text)

            rating_el = card.select_one("div._3LWZlK")
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


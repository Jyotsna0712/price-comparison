import hashlib

from django.shortcuts import render
from django.conf import settings

from .scrapers import search_amazon, search_flipkart


def home(request):
    """
    Render the homepage with centered search bar.
    """
    return render(request, "app/home.html")


def results(request):
    """
    Execute scrapers, aggregate results, and render the results page.
    """
    query = request.GET.get("q", "").strip()
    results = []
    error = None

    if not query:
        error = "Please enter a product name."
    else:
        try:
            amazon_results = search_amazon(query)
            flipkart_results = search_flipkart(query)

            # Normalize: both scrapers return dataclasses with similar fields.
            combined = []
            for item in list(amazon_results) + list(flipkart_results):
                combined.append(
                    {
                        "title": item.title,
                        "price": item.price,
                        "rating": item.rating,
                        "product_url": item.product_url,
                        "image_url": item.image_url,
                        "source": item.source,
                        "price_display": item.price_display,
                    }
                )

            # Sort by price, placing items without price at the end.
            results = sorted(
                combined,
                key=lambda x: (x["price"] is None, x["price"] if x["price"] is not None else 0),
            )

            if not results:
                # If scraping is blocked, show demo cards so the end-to-end UI
                # can still be verified. "View Product" still opens the real
                # product search pages.
                h = hashlib.md5(query.encode("utf-8")).hexdigest()
                seed = int(h[:8], 16)

                amazon_demo_price = 4999 + (seed % 7000)
                flipkart_demo_price = 4799 + ((seed // 7) % 7000)

                encoded = query.replace(" ", "+")
                results = [
                    {
                        "title": f"{query.title()} (Example Deal)",
                        "price": float(amazon_demo_price),
                        "rating": "4.2",
                        "product_url": f"https://www.amazon.in/s?k={encoded}",
                        "image_url": "https://dummyimage.com/600x400/0f172a/ffffff.png&text=Amazon",
                        "source": "Amazon (Demo)",
                        "price_display": f"₹{amazon_demo_price:,.2f}",
                    },
                    {
                        "title": f"{query.title()} (Example Deal)",
                        "price": float(flipkart_demo_price),
                        "rating": "4.1",
                        "product_url": f"https://www.flipkart.com/search?q={encoded}",
                        "image_url": "https://dummyimage.com/600x400/0b5ed7/ffffff.png&text=Flipkart",
                        "source": "Flipkart (Demo)",
                        "price_display": f"₹{flipkart_demo_price:,.2f}",
                    },
                ]
                error = (
                    "No real results found from Amazon or Flipkart. "
                    "Their sites may block automated scraping or load prices via JS. "
                    "Showing demo cards so you can verify the UI flow."
                )
        except Exception as e:
            if getattr(settings, "DEBUG", False):
                error = f"Something went wrong while fetching results: {type(e).__name__}: {e}"
            else:
                error = "Something went wrong while fetching results. Please try again."

    context = {
        "query": query,
        "results": results,
        "error": error,
    }
    return render(request, "app/results.html", context)

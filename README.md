# E-commerce Price Comparison Web Application

This is a Django-based **E-commerce Price Comparison Web Application** inspired by the
`ecommerce-price-comparision` project. Users can search for a product and view
price comparisons from multiple e-commerce websites in a clean Bootstrap UI.

## Tech Stack

- **Backend**: Django (Python), BeautifulSoup, Requests
- **Frontend**: HTML5, CSS3, Bootstrap 5
- **Database**: SQLite (default Django DB)

## Features

- Homepage with centered search bar
- Scrapers for:
  - Amazon (`app/scrapers/amazon_scraper.py`)
  - Flipkart (`app/scrapers/flipkart_scraper.py`)
- Aggregation and normalization of results
- Sorting by price (lowest first)
- Responsive, Bootstrap-based results page with product cards:
  - Image
  - Title
  - Price
  - Rating
  - Source (Amazon / Flipkart)
  - "View Product" button opening in a new tab
- Basic error handling and timeouts

## Getting Started

1. **Clone the repository** (if not already):

```bash
git clone <your-repo-url>
cd price-comparison
```

2. **(Optional but recommended) Create a virtual environment**:

```bash0000
python -m venv venv
venv\Scripts\activate  # Windows
```

3. **Install dependencies**:

```bash
pip install -r requirements.txt
```

4. **Apply database migrations**:

```bash
python manage.py migrate
```

5. **Run the development server**:

```bash
python manage.py runserver
```

6. **Open the app** in your browser:

`http://127.0.0.1:8000/`

## Usage

1. Go to the home page.
2. Enter a product name (e.g. "iPhone 15").
3. Submit the search.
4. View aggregated results from Amazon and Flipkart, sorted by price.

> Note: Scraping relies on the current HTML structure of Amazon and Flipkart.
> If their markup or anti-bot protections change, some results may be empty or incomplete.

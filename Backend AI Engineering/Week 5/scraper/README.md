# FlyRank AI Engineering Internship - Web Scraper Project

A robust, polite, and caching web scraper built in Python to extract book records from [Books to Scrape](https://books.toscrape.com/), featuring robust fault-tolerance, Pydantic data validation, and idempotency.

---

## 🎯 Target Classification (Stage 0)
* **Target site:** Books to Scrape (https://books.toscrape.com)
* **Why:** It is a sandbox site explicitly built for scraping practice ("A fictional bookstore that desperately wants to be scraped" - toscrape.com). It requires no login, no JavaScript, and no API key.
* **Scope:** Only the first 3 catalogue pages (60 books out of 1000 total).
* **Data collected:** title, price, availability, rating, and description for each book — no personal data.
* **robots.txt result:** Requested https://books.toscrape.com/robots.txt — the server returned "404 Not Found". No robots file exists, so there are no automated crawling rules to follow. (Note: a missing file is not permission by itself, it is just a missing file.)
* **Why appropriate:** The site is a public, free practice sandbox with no real user data, created specifically for learning scraping.

I will not reuse this code on another site without checking its rules and terms first.

---

## ⚙️ Installation & Setup

1. Clone the repository:
   ```bash
   git clone [https://github.com/caglaeren/FlyRank-AI.git](https://github.com/caglaeren/FlyRank-AI.git)
   cd scraper 
   ```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🚀 Run Command
Run the pipeline with a single command:
```bash
python src/main.py
```

## 📋 Record Schema (Pydantic)
Every extracted and validated book record conforms to the following schema:

- **title:** ```str``` — Book title.

- **product_url:** ```HttpUrl``` — Canonical absolute URL of the book.

- **price:** str — Raw price text (e.g., "£51.77").

- **price_gbp:** ```float``` — Cleaned numerical price for sorting/comparison.

- **availability**: ```str``` — Stock status text.

- **rating:** ```str``` — Star rating class (e.g., "Three").

- **description:** ```str | None``` — Book description (optional).

- **source_page:**```HttpUrl``` — The catalogue page where the book was found.

- **fetched_at:** ```str``` — UTC timestamp of the fetch event.

## 🤖 Politeness & Reliability Rules
- **User-Agent:** Identifies the scraper clearly with a contact/repository link.

- **Rate Limiting / Delay:** Implements a ```0.5``` second delay on fresh network requests to prevent server flooding.

- **Timeout:** Enforces a strict ```10``` second timeout limit per request.

- **Caching:** Caches all raw HTML pages locally (```cache/```) to avoid redundant server requests.

- **Idempotency:** Re-running the scraper updates existing records safely without duplicating data.

- **Fault Tolerance:** Handles bad/broken pages gracefully (```5xx``` retries, skipping ```404/403``` cleanly) without crashing the pipeline.

## 📊 Run Report (Proof)
Example execution output (```output/run-report.json```):

```
{
    "start_time": "2026-08-13T22:43:15.390508Z",
    "duration_seconds": 0.66,
    "pages_fetched": 1,
    "cache_hits": 63,
    "valid_records": 60,
    "invalid_records": 0,
    "failed_pages": 1
}
```
**Why no browser was needed:** *The data is already in the HTML the server sends, so a browser would only add cost.*


## ⚖️ Ethics Note
Web scraping must be performed responsibly. Always use an official API when one exists; never bypass logins, paywalls, or rate-limit blocks; and collect only what you strictly need.

## ⚠️ Honest Limitation

This scraper is custom-tailored for the structure of the Books to Scrape website. Changes to the target website's DOM structure or CSS selectors would require corresponding updates to the parsing logic.


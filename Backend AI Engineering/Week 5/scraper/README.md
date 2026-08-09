## Target Classification (Stage 0)

- **Target site:** Books to Scrape (https://books.toscrape.com)
- **Why:** It is a sandbox site explicitly built for scraping practice
  ("A fictional bookstore that desperately wants to be scraped" - toscrape.com).
  It requires no login, no JavaScript, and no API key.
- **Scope:** Only the first 3 catalogue pages (60 books out of 1000 total).
- **Data collected:** title, price, availability, rating, and description
  for each book — no personal data.
- **robots.txt result:** Requested https://books.toscrape.com/robots.txt —
  the server returned "404 Not Found". No robots file exists, so there are
  no automated crawling rules to follow. (Note: a missing file is not
  permission by itself, it is just a missing file.)
- **Why appropriate:** The site is a public, free practice sandbox with no
  real user data, created specifically for learning scraping.

I will not reuse this code on another site without checking its rules and terms first.
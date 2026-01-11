# URL Extractor

A simple, fast, and asynchronous web crawler to extract all URLs from a website.

## Features

*   **Asynchronous Crawling:** Uses `asyncio` and `aiohttp` for fast, concurrent crawling.
*   **Subdomain Matching:** Can crawl and extract URLs from the main domain and its subdomains.
*   **Max Pages Limit:** Allows setting a maximum number of pages to crawl.
*   **Command-Line Interface:** Provides a simple CLI to specify the start URL, max pages, and number of workers.
*   **Graceful Shutdown:** Ensures that the crawler stops gracefully when the maximum number of pages is reached or when all URLs have been processed.

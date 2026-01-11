# Gemini Project Context: URL Extractor

## Project Overview

This project is a Python-based asynchronous web crawler designed to extract URLs from a given website. It's built with modern asynchronous libraries to ensure high performance and efficiency. The crawler is designed to be run from the command line and offers several options for controlling the crawling process.

**Main Technologies:**

*   **Language:** Python 3.13
*   **Asynchronous Framework:** `asyncio`
*   **HTTP Client:** `aiohttp`
*   **HTML Parsing:** `BeautifulSoup`
*   **Dependency Management:** `uv` with a `pyproject.toml` file.

**Architecture:**

The crawler uses a worker-based asynchronous architecture. A pool of worker tasks fetches URLs from a shared queue, processes the pages, and adds new links back to the queue. A `CrawlingState` class is used to manage the shared state between the workers, including the set of visited URLs and the total number of pages crawled. This ensures that the `max_pages` limit is strictly enforced and that the crawler terminates gracefully when the crawling process is complete.

## Building and Running

**1. Install Dependencies:**

The project uses `uv` for dependency management. To install the required packages, run the following command:

```bash
uv pip sync pyproject.toml
```

**2. Running the Crawler:**

The crawler is run from the command line using the `main.py` script. The following command-line arguments are available:

*   `start_url`: The URL to start crawling from (required).
*   `--max-pages`: The maximum number of pages to crawl. Use -1 for unlimited (optional, default: -1).
*   `--num-workers`: The number of concurrent workers for async crawling (optional, default: 5).

**Example:**

```bash
# Crawl a website with a maximum of 100 pages and 10 workers
./.venv/bin/python main.py https://example.com --max-pages 100 --num-workers 10
```

**TODO:** Add instructions for running tests once a testing framework is set up.

## Development Conventions

*   **Branching:** Each new feature should be developed in its own branch, created from the `main` branch.
*   **Commits:** Commit messages should be descriptive and follow the conventional commit format (e.g., `feat:`, `fix:`, `docs:`).
*   **Coding Style:** The code should follow the PEP 8 style guide.
*   **Testing:** All new features should be accompanied by tests. (Note: No testing framework is currently in place).

import asyncio
import aiohttp
from urllib.parse import urlparse

from .extractor import extract_links_from_html
from .http import get_page_content_async

def matchsubdomain(base_netloc: str, link_netloc: str):
    """
    Checks if the link's netloc matches the base netloc, allowing for subdomains.
    """
    return link_netloc.endswith(base_netloc)

async def worker(queue: asyncio.Queue, session, base_netloc: str, visited: set, js_links: set, pages_crawled_count: list, max_pages: int):
    """
    A worker that fetches URLs from the queue, processes them, and adds new links back to the queue.
    """
    while True:
        current_url = await queue.get()
        try:
            if current_url is None:
                break

            if current_url in visited or current_url in js_links:
                continue

            if max_pages != -1 and pages_crawled_count[0] >= max_pages:
                continue
                
            if not matchsubdomain(base_netloc, urlparse(current_url).netloc):
                continue
            
            if current_url.endswith('.js'):
                js_links.add(current_url)
                print(f"Found JS file: {current_url}")
                continue

            visited.add(current_url)
            pages_crawled_count[0] += 1
            print(f"Crawling: {current_url} (Crawled: {pages_crawled_count[0]}/{max_pages if max_pages != -1 else 'unlimited'})")

            content, content_type = await get_page_content_async(session, current_url)
            if content:
                links = set()
                if 'html' in content_type:
                    links = await extract_links_from_html(content, current_url)
                
                for link in links:
                    if link not in visited and link not in js_links and matchsubdomain(base_netloc, urlparse(link).netloc):
                        if max_pages != -1 and pages_crawled_count[0] >= max_pages:
                            break
                        await queue.put(link)
        finally:
            queue.task_done()

async def crawl_async(start_url, max_pages=-1, num_workers=5, output_file=None):
    """
    Crawls a website starting from a given URL asynchronously.
    """
    base_netloc = urlparse(start_url).netloc
    queue = asyncio.Queue()
    await queue.put(start_url)
    
    visited = set()
    js_links = set()
    pages_crawled_count = [0]

    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(num_workers):
            task = asyncio.create_task(worker(queue, session, base_netloc, visited, js_links, pages_crawled_count, max_pages))
            tasks.append(task)

        await queue.join()

        for _ in range(num_workers):
            await queue.put(None)

        await asyncio.gather(*tasks, return_exceptions=True)

    print(f"\nCrawled {pages_crawled_count[0]} pages.")
    
    if output_file:
        with open(output_file, 'w') as f:
            for url in sorted(list(visited)):
                f.write(f"{url}\n")
            f.write("\nJavaScript links:\n")
            for url in sorted(list(js_links)):
                f.write(f"{url}\n")
        print(f"Saved {len(visited)} URLs to {output_file}")
        print(f"Saved {len(js_links)} JavaScript files to {output_file}")
    else:
        print("All found URLs:")
        for url in sorted(list(visited)):
            print(url)
            
    print("\nFound JavaScript files:")
    for url in sorted(list(js_links)):
        print(url)

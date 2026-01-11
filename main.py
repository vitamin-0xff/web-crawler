import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import argparse

# --- Asynchronous Version ---

def matchsubdomain(base_netloc: str, link_netloc: str):
    """
    Checks if the link's netloc matches the base netloc, allowing for subdomains.
    """
    return link_netloc.endswith(base_netloc)

class CrawlingState:
    def __init__(self, max_pages):
        self.visited = set()
        self.pages_crawled_count = 0
        self.max_pages = max_pages
        self.lock = asyncio.Lock()
        self.crawling_done = asyncio.Event() # Signal when crawling should stop

async def get_page_content_async(session, url):
    """
    Fetches the content of a web page asynchronously.
    """
    try:
        async with session.get(url, timeout=5) as response:
            response.raise_for_status()
            return await response.text()
    except aiohttp.ClientError as e:
        print(f"Error fetching {url}: {e}")
        return None

async def extract_links(html_content, base_url):
    """
    Extracts all links from the HTML content of a page.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        absolute_link = urljoin(base_url, href)
        parsed_link = urlparse(absolute_link)
        absolute_link = parsed_link.scheme + "://" + parsed_link.netloc + parsed_link.path
        links.add(absolute_link)
    return links

async def worker(queue: asyncio.Queue, session, base_netloc: str, state: CrawlingState):
    """
    A worker that fetches URLs from the queue, processes them, and adds new links back to the queue.
    """
    while not state.crawling_done.is_set():
        current_url = None
        try:
            current_url = await asyncio.wait_for(queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            if state.crawling_done.is_set():
                break
            else:
                continue

        async with state.lock:
            if current_url in state.visited:
                queue.task_done()
                continue
            
            if state.max_pages != -1 and state.pages_crawled_count >= state.max_pages:
                queue.task_done()
                state.crawling_done.set() # Signal that max pages reached
                break

            if not matchsubdomain(base_netloc, urlparse(current_url).netloc):
                queue.task_done()
                continue

            state.visited.add(current_url)
            state.pages_crawled_count += 1
            print(f"Crawling: {current_url} (Crawled: {state.pages_crawled_count}/{state.max_pages if state.max_pages != -1 else 'unlimited'})")

        html_content = await get_page_content_async(session, current_url)
        if html_content:
            links = await extract_links(html_content, current_url)
            for link in links:
                async with state.lock:
                    if state.max_pages != -1 and state.pages_crawled_count >= state.max_pages:
                        state.crawling_done.set() # Signal that max pages reached
                        break
                    if link not in state.visited and matchsubdomain(base_netloc, urlparse(link).netloc):
                        await queue.put(link)
        
        queue.task_done()
    
    # Ensure remaining tasks are marked done if workers exit early due to max_pages
    if current_url is not None:
        queue.task_done()


async def crawl_async(start_url, max_pages=-1, num_workers=5):
    """
    Crawls a website starting from a given URL asynchronously.
    """
    base_netloc = urlparse(start_url).netloc
    queue = asyncio.Queue()
    await queue.put(start_url)
    
    state = CrawlingState(max_pages)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(num_workers):
            task = asyncio.create_task(worker(queue, session, base_netloc, state))
            tasks.append(task)

        # Wait until all initial items are processed and no new items are added for a while
        # Or until max_pages is reached
        while not state.crawling_done.is_set():
            await asyncio.sleep(1) # Allow workers to process
            async with state.lock:
                if queue.empty() and state.pages_crawled_count >= len(state.visited):
                    # No items left to process and no new items added for this cycle
                    break
                if state.max_pages != -1 and state.pages_crawled_count >= state.max_pages:
                    state.crawling_done.set()
                    break


        # Signal all workers to stop
        state.crawling_done.set()
        await asyncio.gather(*tasks, return_exceptions=True) # Wait for all workers to finish

    print(f"\nCrawled {state.pages_crawled_count} pages.")
    print("All found URLs:")
    for url in sorted(list(state.visited)):
        print(url)

def main():
    parser = argparse.ArgumentParser(description="A simple web crawler.")
    parser.add_argument("start_url", help="The URL to start crawling from.")
    parser.add_argument("--max-pages", type=int, default=-1, help="The maximum number of pages to crawl. Use -1 for unlimited.")
    parser.add_argument("--num-workers", type=int, default=5, help="The number of concurrent workers for async crawling.")
    args = parser.parse_args()

    asyncio.run(crawl_async(args.start_url, args.max_pages, args.num_workers))

if __name__ == "__main__":
    main()
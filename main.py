import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import argparse
import re

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

async def get_page_content_async(session, url):
    """
    Fetches the content of a web page asynchronously.
    """
    try:
        async with session.get(url, timeout=5) as response:
            response.raise_for_status()
            content = await response.text()
            return content, response.headers.get('Content-Type', '')
    except aiohttp.ClientError as e:
        print(f"Error fetching {url}: {e}")
        return None, None

async def extract_links_from_html(html_content, base_url):
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
    
    for script_tag in soup.find_all('script'):
        script_content = script_tag.string
        if script_content:
            script_links = await extract_links_from_script(script_content, base_url)
            links.update(script_links)
            
    return links

async def extract_links_from_script(script_content, base_url):
    """
    Extracts all links from the JavaScript content of a page.
    """
    links = set()
    
    # Regex for fetch, axios and generic urls
    patterns = [
        r'fetch\s*\(\s*[\'\`"]([^\'\`"]+)[\'\`"]\s*\)',
        r'axios\.get\s*\(\s*[\'\`"]([^\'\`"]+)[\'\`"]\s*\)',
        r'[\'\`"](https?://[^\'\`"]+|(?:/[^\'\`"]+))[\'\`"]'
    ]
    
    for pattern in patterns:
        for url in re.findall(pattern, script_content):
            absolute_link = urljoin(base_url, url)
            parsed_link = urlparse(absolute_link)
            absolute_link = parsed_link.scheme + "://" + parsed_link.netloc + parsed_link.path
            links.add(absolute_link)
            
    return links

async def worker(queue: asyncio.Queue, session, base_netloc: str, state: CrawlingState):
    """
    A worker that fetches URLs from the queue, processes them, and adds new links back to the queue.
    """
    while True:
        current_url = await queue.get()
        if current_url is None:
            break

        async with state.lock:
            if current_url in state.visited:
                queue.task_done()
                continue
            
            if state.max_pages != -1 and state.pages_crawled_count >= state.max_pages:
                queue.task_done()
                continue

            if not matchsubdomain(base_netloc, urlparse(current_url).netloc):
                queue.task_done()
                continue

            state.visited.add(current_url)
            state.pages_crawled_count += 1
            print(f"Crawling: {current_url} (Crawled: {state.pages_crawled_count}/{state.max_pages if state.max_pages != -1 else 'unlimited'})")

        content, content_type = await get_page_content_async(session, current_url)
        if content:
            links = set()
            if 'html' in content_type:
                links = await extract_links_from_html(content, current_url)
            # Add other content type handlers here if needed
            
            for link in links:
                async with state.lock:
                    if state.max_pages != -1 and state.pages_crawled_count >= state.max_pages:
                        break
                    if link not in state.visited and matchsubdomain(base_netloc, urlparse(link).netloc):
                        await queue.put(link)
        
        queue.task_done()

async def crawl_async(start_url, max_pages=-1, num_workers=5, output_file=None):
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

        await queue.join()

        for _ in range(num_workers):
            await queue.put(None)

        await asyncio.gather(*tasks, return_exceptions=True)

    print(f"\nCrawled {state.pages_crawled_count} pages.")
    
    if output_file:
        with open(output_file, 'w') as f:
            for url in sorted(list(state.visited)):
                f.write(f"{url}\n")
        print(f"Saved {len(state.visited)} URLs to {output_file}")
    else:
        print("All found URLs:")
        for url in sorted(list(state.visited)):
            print(url)

def main():
    parser = argparse.ArgumentParser(description="A simple web crawler.")
    parser.add_argument("start_url", help="The URL to start crawling from.")
    parser.add_argument("--max-pages", type=int, default=-1, help="The maximum number of pages to crawl. Use -1 for unlimited.")
    parser.add_argument("--num-workers", type=int, default=5, help="The number of concurrent workers for async crawling.")
    parser.add_argument("--output-file", help="The file to save the extracted URLs to.")
    args = parser.parse_args()

    asyncio.run(crawl_async(args.start_url, args.max_pages, args.num_workers, args.output_file))

if __name__ == "__main__":
    main()
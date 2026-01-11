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
    
    for script_tag in soup.find_all('script', src=True):
        src = script_tag['src']
        absolute_link = urljoin(base_url, src)
        parsed_link = urlparse(absolute_link)
        absolute_link = parsed_link.scheme + "://" + parsed_link.netloc + parsed_link.path
        links.add(absolute_link)
            
    return links

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

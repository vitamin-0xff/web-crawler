import asyncio
import aiohttp

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

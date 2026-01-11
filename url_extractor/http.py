import asyncio
import aiohttp
from functools import wraps

def retry(attempts=3, delay=1, backoff=2):
    """
    A decorator for retrying a function with exponential backoff.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal delay
            for attempt in range(attempts):
                try:
                    return await func(*args, **kwargs)
                except (aiohttp.ClientConnectorError, aiohttp.ClientResponseError, asyncio.TimeoutError) as e:
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    delay *= backoff
            return await func(*args, **kwargs) # Last attempt
        return wrapper
    return decorator

@retry(attempts=3, delay=1, backoff=2)
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
        raise e

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

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

async def extract_links_from_script(script_content, base_url):
    """
    Extracts all links from the JavaScript content of a page.
    """
    links = set()
    
    # Regex for fetch, axios and generic urls
    patterns = [
        r'fetch\s*\(\s*[\'\`"]([^\'\`"]+)[\'\`"]\s*\)',
        r'axios\.get\s*\(\s*[\'\`"]([^\'\`"]+)[\'\`"]\s*\)',
        r'[\'\`"](https?://[^\'\`"]+|(?:\/[^\'\`"]+))[\'\`"]'
    ]
    
    for pattern in patterns:
        for url in re.findall(pattern, script_content):
            absolute_link = urljoin(base_url, url)
            parsed_link = urlparse(absolute_link)
            absolute_link = parsed_link.scheme + "://" + parsed_link.netloc + parsed_link.path
            links.add(absolute_link)
            
    return links

import argparse
import asyncio
from url_extractor.crawler import crawl_async

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
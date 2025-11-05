# Main entry point for running the docs crawler

from crawlers.docs_crawler import FastnDocsCrawler

def main():
    crawler = FastnDocsCrawler()
    print("Starting to crawl docs.fastn.ai...")
    content = crawler.start_crawling()
    print(f"\nCrawling completed. Found {len(content)} pages.")
    crawler.save_to_file()
    print("\nContent saved to docs_content.json")

if __name__ == "__main__":
    main()
# This module crawls the fastn docs website and extracts all the content from each page

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import os

class FastnDocsCrawler:
    def __init__(self):
        self.base_url = "https://docs.fastn.ai"
        self.visited_urls = set()
        self.docs_content = {}

    def is_valid_url(self, url):
        parsed = urlparse(url)
        return bool(parsed.netloc) and parsed.netloc == "docs.fastn.ai"

    def extract_content(self, soup):
        main_content = soup.find('main')
        if not main_content:
            return None

        content = {
            'text': main_content.get_text(separator=' ', strip=True),
            'headings': [h.get_text(strip=True) for h in main_content.find_all(['h1', 'h2', 'h3', 'h4'])],
            'code_blocks': [code.get_text(strip=True) for code in main_content.find_all('code')]
        }
        return content

    def get_links(self, soup, current_url):
        links = []
        for a in soup.find_all('a', href=True):
            url = urljoin(current_url, a['href'])
            if self.is_valid_url(url) and url not in self.visited_urls:
                links.append(url)
        return links

    def crawl(self, url):
        if url in self.visited_urls:
            return

        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                content = self.extract_content(soup)
                
                if content:
                    self.docs_content[url] = content
                    self.visited_urls.add(url)
                    
                    links = self.get_links(soup, url)
                    for link in links:
                        self.crawl(link)
                        
        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")

    def start_crawling(self):
        self.crawl(self.base_url)
        return self.docs_content

    def save_to_file(self, filename='docs_content.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.docs_content, f, indent=2)

if __name__ == "__main__":
    crawler = FastnDocsCrawler()
    content = crawler.start_crawling()
    
    # Print content to terminal
    for url, data in content.items():
        print(f"\nURL: {url}")
        print("=" * 80)
        print("Content:")
        print(data['text'][:500] + "...")  # Print first 500 chars
        print("\nHeadings:")
        print("\n".join(data['headings']))
        print("-" * 80)
    
    # Save content to file
    crawler.save_to_file('docs_content.json')
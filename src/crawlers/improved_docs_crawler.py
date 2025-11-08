# Improved GitBook documentation crawler with better content extraction
# Focuses on main content, removes navigation/sidebar noise

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import json
import os
import time
from typing import Set, Dict, Any


class ImprovedGitBookCrawler:
    """
    Enhanced crawler specifically for GitBook documentation
    - Better content extraction (removes nav, sidebar, footer)
    - Handles pagination and navigation
    - Cleans up formatting for better AI understanding
    """
    
    def __init__(self, base_url: str = "https://docs.fastn.ai"):
        self.base_url = base_url
        self.visited_urls: Set[str] = set()
        self.docs_content: Dict[str, Dict[str, Any]] = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and within domain"""
        # Remove fragment (anchor)
        url, _ = urldefrag(url)
        
        parsed = urlparse(url)
        base_parsed = urlparse(self.base_url)
        
        # Must be same domain and scheme
        if parsed.netloc != base_parsed.netloc:
            return False
        
        # Skip certain patterns
        skip_patterns = ['#', 'javascript:', 'mailto:', '.pdf', '.zip']
        if any(pattern in url.lower() for pattern in skip_patterns):
            return False
        
        return True
    
    def extract_main_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract only the main documentation content
        GitBook typically uses: <main>, <article>, or specific classes
        """
        
        # Try different selectors for GitBook content
        main_content = None
        
        # Priority order for content extraction
        selectors = [
            'main',  # Most GitBook sites use <main>
            'article',
            '.markdown-section',  # Common GitBook class
            '[role="main"]',
            '.page-content',
            '#content'
        ]
        
        for selector in selectors:
            main_content = soup.select_one(selector)
            if main_content:
                print(f"  Found content using selector: {selector}")
                break
        
        if not main_content:
            # Fallback to body
            main_content = soup.find('body')
            print("  Using fallback: body tag")
        
        if not main_content:
            return None
        
        # Remove unwanted elements (navigation, sidebar, footer, etc.)
        unwanted_selectors = [
            'nav',
            'header',
            'footer',
            '.sidebar',
            '.navigation',
            '.breadcrumb',
            '.page-header',
            '.page-footer',
            '[role="navigation"]',
            '.toc',
            '.table-of-contents',
            'script',
            'style',
            'noscript',
            '.ad',
            '.advertisement'
        ]
        
        for selector in unwanted_selectors:
            for element in main_content.select(selector):
                element.decompose()
        
        # Extract structured content
        content = {
            'text': '',
            'headings': [],
            'code_blocks': []
        }
        
        # Get all text (cleaned)
        text = main_content.get_text(separator=' ', strip=True)
        # Clean up multiple spaces and newlines
        text = ' '.join(text.split())
        content['text'] = text
        
        # Extract headings with hierarchy
        for heading in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = heading.get_text(strip=True)
            if heading_text:
                content['headings'].append({
                    'level': heading.name,
                    'text': heading_text
                })
        
        # Extract code blocks
        for code in main_content.find_all(['code', 'pre']):
            code_text = code.get_text(strip=True)
            if code_text and len(code_text) > 10:  # Skip tiny code snippets
                content['code_blocks'].append(code_text)
        
        # Add page title
        title_tag = soup.find('title')
        if title_tag:
            content['title'] = title_tag.get_text(strip=True)
        
        # Add meta description if available
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            content['description'] = meta_desc['content']
        
        return content
    
    def get_links(self, soup: BeautifulSoup, current_url: str) -> Set[str]:
        """Extract all valid documentation links"""
        links = set()
        
        for a in soup.find_all('a', href=True):
            url = urljoin(current_url, a['href'])
            url, _ = urldefrag(url)  # Remove anchors
            
            if self.is_valid_url(url) and url not in self.visited_urls:
                links.add(url)
        
        return links
    
    def crawl(self, url: str, max_pages: int = 1000) -> None:
        """
        Crawl documentation starting from given URL
        
        Args:
            url: Starting URL
            max_pages: Maximum pages to crawl (safety limit)
        """
        to_visit = {url}
        
        while to_visit and len(self.visited_urls) < max_pages:
            current_url = to_visit.pop()
            
            if current_url in self.visited_urls:
                continue
            
            try:
                print(f"\n[{len(self.visited_urls) + 1}] Crawling: {current_url}")
                
                response = self.session.get(current_url, timeout=10)
                response.raise_for_status()
                
                self.visited_urls.add(current_url)
                
                soup = BeautifulSoup(response.text, 'html.parser')
                content = self.extract_main_content(soup)
                
                if content and content['text']:
                    self.docs_content[current_url] = content
                    print(f"  ✓ Extracted {len(content['text'])} chars, "
                          f"{len(content['headings'])} headings, "
                          f"{len(content['code_blocks'])} code blocks")
                else:
                    print(f"  ✗ No content extracted")
                
                # Get new links
                new_links = self.get_links(soup, current_url)
                to_visit.update(new_links)
                
                # Be polite - small delay
                time.sleep(0.5)
                
            except requests.exceptions.RequestException as e:
                print(f"  ✗ Error: {str(e)}")
                self.visited_urls.add(current_url)
            except Exception as e:
                print(f"  ✗ Unexpected error: {str(e)}")
                self.visited_urls.add(current_url)
    
    def save_to_json(self, filename: str = "docs_content.json") -> None:
        """Save crawled content to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.docs_content, f, indent=2, ensure_ascii=False)
            print(f"\n✓ Saved {len(self.docs_content)} pages to {filename}")
            print(f"  File size: {os.path.getsize(filename) / 1024 / 1024:.2f} MB")
        except Exception as e:
            print(f"✗ Error saving file: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get crawling statistics"""
        total_text_length = sum(len(doc['text']) for doc in self.docs_content.values())
        total_headings = sum(len(doc['headings']) for doc in self.docs_content.values())
        total_code_blocks = sum(len(doc['code_blocks']) for doc in self.docs_content.values())
        
        return {
            'total_pages': len(self.docs_content),
            'total_text_chars': total_text_length,
            'total_headings': total_headings,
            'total_code_blocks': total_code_blocks,
            'avg_text_per_page': total_text_length // len(self.docs_content) if self.docs_content else 0
        }


def main():
    """Main crawler function"""
    print("="*70)
    print("IMPROVED FASTN.AI DOCUMENTATION CRAWLER")
    print("="*70)
    
    crawler = ImprovedGitBookCrawler("https://docs.fastn.ai")
    
    print("\nStarting crawl from: https://docs.fastn.ai")
    print("This may take several minutes...")
    
    start_time = time.time()
    crawler.crawl("https://docs.fastn.ai", max_pages=1000)
    elapsed = time.time() - start_time
    
    print("\n" + "="*70)
    print("CRAWL COMPLETE")
    print("="*70)
    
    stats = crawler.get_stats()
    print(f"\nStatistics:")
    print(f"  Pages crawled: {stats['total_pages']}")
    print(f"  Total text: {stats['total_text_chars']:,} characters")
    print(f"  Total headings: {stats['total_headings']}")
    print(f"  Total code blocks: {stats['total_code_blocks']}")
    print(f"  Average text per page: {stats['avg_text_per_page']:,} characters")
    print(f"  Time taken: {elapsed:.1f} seconds")
    print(f"  Pages per second: {stats['total_pages'] / elapsed:.2f}")
    
    # Save to file
    output_file = os.path.join(os.path.dirname(__file__), 'docs_content.json')
    crawler.save_to_json(output_file)
    
    print("\n" + "="*70)
    print("DONE! You can now use the updated docs_content.json")
    print("="*70)


if __name__ == "__main__":
    main()


import scrapy
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import xml.etree.ElementTree as ET
import requests
import json
from urllib.parse import urljoin, urlparse

class WebsiteCrawler:
    def __init__(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        
    def scan_for_urls(self, base_url):
        try:
            response = requests.get(base_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                domain = urlparse(base_url).netloc
                urls = set()
                
                for link in soup.find_all('a', href=True):
                    url = urljoin(base_url, link['href'])
                    if urlparse(url).netloc == domain:  # Only include URLs from same domain
                        urls.add(url)
                return list(urls)
        except Exception as e:
            print(f"Error scanning URLs: {e}")
            return []

    def parse_sitemap(self, base_url):
        urls = set()
        try:
            # Try common sitemap URLs
            sitemap_urls = [
                urljoin(base_url, '/sitemap.xml'),
                urljoin(base_url, '/sitemap_index.xml')
            ]
            
            for sitemap_url in sitemap_urls:
                response = requests.get(sitemap_url)
                if response.status_code == 200:
                    root = ET.fromstring(response.content)
                    for loc in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
                        urls.add(loc.text)
                    break
            
            # If no URLs found in sitemap, scan the website
            if not urls:
                print("No sitemap found, scanning website for URLs...")
                urls.update(self.scan_for_urls(base_url))
        except Exception as e:
            print(f"Error parsing sitemap: {e}")
            # Fallback to manual scanning
            print("Falling back to manual website scanning...")
            urls.update(self.scan_for_urls(base_url))
        return list(urls)
    
    def crawl_url(self, url):
        try:
            with webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.chrome_options) as driver:
                driver.get(url)
                content = driver.page_source
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract text content
                text_content = ' '.join([p.get_text() for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])])
                
                # Extract links
                links = [urljoin(url, a.get('href')) for a in soup.find_all('a', href=True)]
                
                return {
                    'url': url,
                    'content': text_content,
                    'links': links
                }
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return None

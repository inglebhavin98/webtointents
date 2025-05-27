import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class WebsiteCrawler:
    def __init__(self):
        print(f"*** WebsiteCrawler.__init__")
        # Initialize Chrome options for headless browsing
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')

    def crawl(self, base_url: str) -> Dict[str, Any]:
        print(f"*** WebsiteCrawler.crawl")
        """Crawl a website starting from the base URL and return a dictionary of page data."""
        logger.info(f"Starting crawl from base URL: {base_url}")
        
        # First get all URLs from sitemap or generate one
        urls = self.parse_sitemap(base_url)
        if not urls:
            logger.warning("No URLs found to crawl")
            return {}
            
        # Limit to first 5 pages for testing
        urls = urls[:5]
        logger.info(f"Limited crawl to {len(urls)} pages")
            
        # Crawl each URL and collect data
        pages = {}
        for url in urls:
            try:
                logger.info(f"Crawling URL: {url}")
                page_data = self.crawl_url(url)
                if page_data:
                    pages[url] = page_data
            except Exception as e:
                logger.error(f"Error crawling {url}: {str(e)}")
                continue
                
        logger.info(f"Completed crawling {len(pages)} pages")
        return pages

    def create_sitemap(self, base_url):
        print(f"*** WebsiteCrawler.create_sitemap")
        """Scan website and create sitemap.xml file"""
        print(f"Starting sitemap creation for {base_url}")
        visited = set()
        to_visit = {base_url}
        domain = urlparse(base_url).netloc
        
        # Configure session
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        session.verify = False  # Disable SSL verification
        
        while to_visit:
            url = to_visit.pop()
            if url in visited:
                continue

            try:
                print(f"Scanning URL: {url}")
                response = session.get(url, timeout=30, allow_redirects=True)
                if response.status_code == 200:
                    visited.add(url)
                    soup = BeautifulSoup(response.content, 'html.parser')

                    for link in soup.find_all('a', href=True):
                        next_url = urljoin(url, link['href'])
                        parsed_next_url = urlparse(next_url)
                        if (parsed_next_url.netloc == domain and 
                            next_url not in visited and 
                            not next_url.endswith(('.pdf', '.jpg', '.png', '.gif', '.css', '.js')) and
                            '#' not in next_url):  # Skip anchor links
                            print(f"Found new URL: {next_url}")
                            to_visit.add(next_url)
            except Exception as e:
                print(f"Error scanning {url}: {str(e)}")
                continue

        # Create sitemap XML
        root = ET.Element("urlset")
        root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

        for url in visited:
            url_elem = ET.SubElement(root, "url")
            loc = ET.SubElement(url_elem, "loc")
            loc.text = url

        tree = ET.ElementTree(root)
        os.makedirs('sitemaps', exist_ok=True)
        sitemap_path = os.path.join('sitemaps', f"{domain.replace('.', '_')}_sitemap.xml")
        tree.write(sitemap_path, encoding='utf-8', xml_declaration=True)

        print(f"Sitemap created with {len(visited)} URLs!")
        return sitemap_path, list(visited)

    def generate_sitemap(self, base_url):
        print(f"*** WebsiteCrawler.generate_sitemap")
        """Generate sitemap by crawling the website"""
        print("Generating sitemap...")
        visited = set()
        to_visit = {base_url}
        domain = urlparse(base_url).netloc
        
        # Configure requests session with proper headers and redirect handling
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        while to_visit:
            url = to_visit.pop()
            if url in visited:
                continue

            try:
                print(f"Checking URL: {url}")
                response = session.get(url, timeout=30, allow_redirects=True, verify=False)
                if response.status_code == 200:
                    visited.add(url)
                    soup = BeautifulSoup(response.content, 'html.parser')

                    for link in soup.find_all('a', href=True):
                        next_url = urljoin(url, link['href'])
                        if urlparse(next_url).netloc == domain and next_url not in visited:
                            to_visit.add(next_url)
            except Exception as e:
                print(f"Error scanning {url}: {e}")

        # Generate sitemap.xml
        sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        for url in visited:
            sitemap_content += f'  <url>\n    <loc>{url}</loc>\n  </url>\n'
        sitemap_content += '</urlset>'

        with open('sitemap.xml', 'w') as f:
            f.write(sitemap_content)

        return list(visited)

    def parse_sitemap(self, base_url):
        print(f"*** WebsiteCrawler.parse_sitemap")
        """Parse existing sitemap.xml or generate new one"""
        if not os.path.exists('sitemap.xml'):
            return self.generate_sitemap(base_url)

        try:
            tree = ET.parse('sitemap.xml')
            root = tree.getroot()
            urls = [loc.text for loc in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
            return urls
        except Exception as e:
            print(f"Error parsing sitemap: {e}")
            return self.generate_sitemap(base_url)

    def crawl_url(self, url, max_retries=3):
        print(f"*** WebsiteCrawler.crawl_url")
        driver = None
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1}/{max_retries} for URL: {url}")

                self.chrome_options = Options()
                self.chrome_options.add_argument('--headless=new')
                self.chrome_options.add_argument('--no-sandbox')
                self.chrome_options.add_argument('--disable-dev-shm-usage')
                self.chrome_options.add_argument('--disable-gpu')
                self.chrome_options.add_argument('--window-size=1920,1080')
                self.chrome_options.add_argument('--ignore-certificate-errors')
                self.chrome_options.add_argument('--disable-extensions')
                self.chrome_options.add_argument('--disable-notifications')
                self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=self.chrome_options)
                driver.set_page_load_timeout(30)

                print(f"Loading page: {url}")
                driver.get(url)

                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                content = driver.page_source
                soup = BeautifulSoup(content, 'html.parser')

                # Basic metadata
                title = soup.title.string if soup.title else ''
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                description = meta_desc['content'] if meta_desc else ''
                canonical = soup.find('link', attrs={'rel': 'canonical'})
                canonical_url = canonical['href'] if canonical else url
                domain = urlparse(url).netloc

                # Content structure
                headers = {
                    'h1': [h.get_text().strip() for h in soup.find_all('h1')],
                    'h2': [h.get_text().strip() for h in soup.find_all('h2')],
                    'h3': [h.get_text().strip() for h in soup.find_all('h3')]
                }

                # Extract main content sections
                main_content = []
                for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    text = p.get_text().strip()
                    if text:
                        main_content.append({
                            'type': p.name,
                            'text': text
                        })

                # Extract FAQs if present
                faqs = []
                faq_section = soup.find(['div', 'section'], class_=lambda x: x and ('faq' in x.lower() or 'faqs' in x.lower()))
                if faq_section:
                    for q in faq_section.find_all(['h3', 'h4', 'strong']):
                        question = q.get_text().strip()
                        answer = q.find_next(['p', 'div'])
                        if answer:
                            faqs.append({
                                'question': question,
                                'answer': answer.get_text().strip()
                            })

                # Extract forms and their fields
                forms = []
                for form in soup.find_all('form'):
                    form_data = {
                        'action': form.get('action', ''),
                        'method': form.get('method', ''),
                        'fields': []
                    }
                    for field in form.find_all(['input', 'textarea', 'select']):
                        field_data = {
                            'type': field.name,
                            'name': field.get('name', ''),
                            'id': field.get('id', ''),
                            'placeholder': field.get('placeholder', ''),
                            'required': field.get('required', False)
                        }
                        form_data['fields'].append(field_data)
                    forms.append(form_data)

                # Collect navigation links
                internal_links = set()
                external_links = set()
                for link in soup.find_all('a', href=True):
                    next_url = urljoin(url, link['href'])
                    parsed_url = urlparse(next_url)
                    if parsed_url.netloc == domain:
                        internal_links.add(next_url)
                    else:
                        external_links.add(next_url)

                # Determine page type based on content
                page_type = 'unknown'
                if faqs:
                    page_type = 'faq'
                elif forms:
                    page_type = 'form'
                elif any('product' in url.lower() for url in [url, title, description]):
                    page_type = 'product'
                elif any('contact' in url.lower() for url in [url, title, description]):
                    page_type = 'contact'
                elif any('about' in url.lower() for url in [url, title, description]):
                    page_type = 'about'

                if driver:
                    driver.quit()

                return {
                    'url': url,
                    'domain': domain,
                    'metadata': {
                        'title': title,
                        'description': description,
                        'canonical_url': canonical_url,
                        'page_type': page_type
                    },
                    'structure': {
                        'headers': headers,
                        'main_content': main_content,
                        'faqs': faqs,
                        'forms': forms
                    },
                    'navigation': {
                        'internal_links': list(internal_links),
                        'external_links': list(external_links)
                    }
                }

            except Exception as e:
                print(f"Error crawling {url} (attempt {attempt + 1}): {str(e)}")
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
                if attempt == max_retries - 1:
                    return None
                time.sleep(2)
                continue

            finally:
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
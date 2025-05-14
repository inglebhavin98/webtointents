import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
import os

class WebsiteCrawler:
    def __init__(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')

    def create_sitemap(self, base_url):
        """Scan website and create sitemap.xml file"""
        visited = set()
        to_visit = {base_url}
        domain = urlparse(base_url).netloc

        while to_visit:
            url = to_visit.pop()
            if url in visited:
                continue

            try:
                response = requests.get(url)
                if response.status_code == 200:
                    visited.add(url)
                    soup = BeautifulSoup(response.content, 'html.parser')

                    for link in soup.find_all('a', href=True):
                        next_url = urljoin(url, link['href'])
                        if (urlparse(next_url).netloc == domain and 
                            next_url not in visited and 
                            not next_url.endswith(('.pdf', '.jpg', '.png'))):
                            to_visit.add(next_url)
            except Exception as e:
                print(f"Error scanning {url}: {e}")

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

        return sitemap_path, list(visited)

    def generate_sitemap(self, base_url):
        """Generate sitemap by crawling the website"""
        print("Generating sitemap...")
        visited = set()
        to_visit = {base_url}
        domain = urlparse(base_url).netloc

        while to_visit:
            url = to_visit.pop()
            if url in visited:
                continue

            try:
                response = requests.get(url)
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

    def crawl_url(self, url):
        try:
            with webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.chrome_options) as driver:
                driver.get(url)
                content = driver.page_source
                soup = BeautifulSoup(content, 'html.parser')

                title = soup.title.string if soup.title else ''
                headers = {
                    'h1': [h.get_text() for h in soup.find_all('h1')],
                    'h2': [h.get_text() for h in soup.find_all('h2')],
                    'h3': [h.get_text() for h in soup.find_all('h3')]
                }

                text_content = ' '.join([p.get_text() for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])])
                domain = urlparse(url).netloc

                meta_desc = soup.find('meta', attrs={'name': 'description'})
                description = meta_desc['content'] if meta_desc else ''

                return {
                    'url': url,
                    'domain': domain,
                    'metadata': {
                        'title': title,
                        'description': description
                    },
                    'structure': {
                        'headers': headers,
                        'main_content': text_content
                    }
                }
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return None
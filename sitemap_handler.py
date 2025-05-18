import xml.etree.ElementTree as ET
import requests
from urllib.parse import urlparse
from typing import List, Dict, Any
import logging
from collections import defaultdict
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class SitemapHandler:
    def __init__(self):
        """Initialize the sitemap handler."""
        self.namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    
    def fetch_sitemap(self, sitemap_url: str) -> str:
        """Fetch sitemap content from URL."""
        try:
            response = requests.get(sitemap_url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Error fetching sitemap: {str(e)}")
            raise
    
    def validate_xml(self, content: str) -> str:
        """Validate and clean XML content."""
        try:
            # Log the first 1000 characters of the content for debugging
            logger.debug(f"Raw content (first 1000 chars): {content[:1000]}")
            
            # Remove any BOM or special characters at the start
            content = content.lstrip('\ufeff')
            
            # Check if content is empty
            if not content.strip():
                raise ValueError("Empty sitemap content")
            
            # Try to parse the XML to validate it
            try:
                ET.fromstring(content)
            except ET.ParseError as e:
                # If parsing fails, try to clean the content
                logger.warning(f"Initial XML parsing failed: {str(e)}. Attempting to clean content...")
                
                # Log the problematic line and column
                line_num = int(str(e).split('line')[1].split(',')[0])
                col_num = int(str(e).split('column')[1].split()[0])
                logger.debug(f"Error at line {line_num}, column {col_num}")
                
                # Get the problematic line
                lines = content.split('\n')
                if 0 <= line_num - 1 < len(lines):
                    problem_line = lines[line_num - 1]
                    logger.debug(f"Problematic line: {problem_line}")
                    logger.debug(f"Problem area: {problem_line[max(0, col_num-20):col_num+20]}")
                
                # Remove any non-XML content before the first <
                content = content[content.find('<'):]
                
                # Remove any content after the last >
                content = content[:content.rfind('>')+1]
                
                # Log the cleaned content
                logger.debug(f"Cleaned content (first 1000 chars): {content[:1000]}")
                
                # Try parsing again
                try:
                    ET.fromstring(content)
                except ET.ParseError as e2:
                    logger.error(f"Failed to parse even after cleaning: {str(e2)}")
                    raise ValueError(f"Could not parse XML even after cleaning: {str(e2)}")
            
            return content
        except Exception as e:
            logger.error(f"Error validating XML: {str(e)}")
            raise ValueError(f"Invalid XML content: {str(e)}")
    
    def parse_sitemap(self, sitemap_content: str) -> List[str]:
        """Parse sitemap XML content and extract URLs."""
        try:
            # Validate and clean the XML content
            clean_content = self.validate_xml(sitemap_content)
            root = ET.fromstring(clean_content)
            urls = []
            
            # Handle both sitemap index and regular sitemaps
            if root.tag.endswith('sitemapindex'):
                # This is a sitemap index
                for sitemap in root.findall('.//ns:sitemap/ns:loc', self.namespace):
                    sub_sitemap_url = sitemap.text
                    if sub_sitemap_url:
                        try:
                            sub_content = self.fetch_sitemap(sub_sitemap_url)
                            urls.extend(self.parse_sitemap(sub_content))
                        except Exception as e:
                            logger.warning(f"Error processing sub-sitemap {sub_sitemap_url}: {str(e)}")
                            continue
            else:
                # This is a regular sitemap
                for url in root.findall('.//ns:url/ns:loc', self.namespace):
                    if url.text:
                        urls.append(url.text)
            
            # Validate URLs
            valid_urls = []
            for url in urls:
                try:
                    parsed = urlparse(url)
                    if parsed.scheme and parsed.netloc:
                        valid_urls.append(url)
                    else:
                        logger.warning(f"Invalid URL found in sitemap: {url}")
                except Exception as e:
                    logger.warning(f"Error parsing URL {url}: {str(e)}")
            
            if not valid_urls:
                raise ValueError("No valid URLs found in sitemap")
            
            return valid_urls
        except Exception as e:
            logger.error(f"Error parsing sitemap: {str(e)}")
            raise
    
    def create_url_hierarchy(self, urls: List[str]) -> Dict[str, Any]:
        """Create a hierarchical structure from URLs."""
        hierarchy = defaultdict(lambda: {'children': {}, 'urls': []})
        
        for url in urls:
            try:
                parsed = urlparse(url)
                path_parts = parsed.path.strip('/').split('/')
                
                current = hierarchy
                current_path = []
                
                for part in path_parts:
                    current_path.append(part)
                    if part not in current:
                        current[part] = {'children': {}, 'urls': []}
                    current = current[part]['children']
                
                # Add the full URL to the deepest level
                current_path_str = '/'.join(current_path)
                if current_path_str:
                    hierarchy[current_path[0]]['urls'].append(url)
            except Exception as e:
                logger.warning(f"Error processing URL {url}: {str(e)}")
                continue
        
        return self._format_hierarchy(hierarchy)
    
    def _format_hierarchy(self, hierarchy: Dict) -> List[Dict[str, Any]]:
        """Format the hierarchy for UI display."""
        result = []
        
        for key, value in hierarchy.items():
            node = {
                'id': key,
                'label': key,
                'urls': value['urls'],
                'children': self._format_hierarchy(value['children']) if value['children'] else []
            }
            result.append(node)
        
        return result
    
    def process_sitemap(self, sitemap_input: str) -> Dict[str, Any]:
        """Process sitemap input (URL or content) and return URL hierarchy."""
        try:
            # Check if input is a URL
            if sitemap_input.startswith(('http://', 'https://')):
                content = self.fetch_sitemap(sitemap_input)
            else:
                content = sitemap_input
            
            # Parse sitemap and create hierarchy
            urls = self.parse_sitemap(content)
            hierarchy = self.create_url_hierarchy(urls)
            
            if not urls:
                raise ValueError("No valid URLs found in sitemap")
            
            return {
                'urls': urls,
                'hierarchy': hierarchy,
                'total_urls': len(urls)
            }
        except Exception as e:
            logger.error(f"Error processing sitemap: {str(e)}")
            raise 
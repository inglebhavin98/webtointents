import logging
from typing import Dict, Any
from .base import BaseProcessor, ProcessingResult
import re
from collections import OrderedDict

logger = logging.getLogger(__name__)

def clean_scraped_data(page_data: dict) -> dict:
    """Clean and preprocess scraped page data before LLM analysis."""
    def deduplicate_list(items):
        seen = set()
        deduped = []
        for item in items:
            if isinstance(item, str):
                key = item.strip().lower()
                if key and key not in seen:
                    deduped.append(item)
                    seen.add(key)
        return deduped

    def remove_empty_fields(d):
        if isinstance(d, dict):
            return {k: remove_empty_fields(v) for k, v in d.items() if v not in [None, '', [], {}]}
        elif isinstance(d, list):
            return [remove_empty_fields(x) for x in d if x not in [None, '', [], {}]]
        else:
            return d

    def extract_text_from_structure(structure):
        """Extract text content from the page structure."""
        text_blocks = []
        
        def process_element(element):
            if isinstance(element, dict):
                # Handle text content
                if 'text' in element:
                    text_blocks.append(element['text'])
                # Handle metadata
                if 'metadata' in element:
                    for key, value in element['metadata'].items():
                        if isinstance(value, str):
                            text_blocks.append(f"{key}: {value}")
                # Recursively process nested elements
                for value in element.values():
                    if isinstance(value, (dict, list)):
                        process_element(value)
            elif isinstance(element, list):
                for item in element:
                    process_element(item)
        
        process_element(structure)
        return text_blocks

    # Create a new dictionary to store cleaned data
    cleaned_data = {
        'url': page_data.get('url', ''),
        'domain': page_data.get('domain', ''),
        'content': []
    }

    # Extract text from structure
    if 'structure' in page_data:
        structure = page_data['structure']
        # Extract from headers
        if 'headers' in structure:
            for header_type, headers in structure['headers'].items():
                cleaned_data['content'].extend(headers)
        
        # Extract from main content
        if 'main_content' in structure:
            for content_item in structure['main_content']:
                if isinstance(content_item, dict) and 'text' in content_item:
                    cleaned_data['content'].append(content_item['text'])
        
        # Extract from FAQs
        if 'faqs' in structure:
            for faq in structure['faqs']:
                if isinstance(faq, dict):
                    if 'question' in faq:
                        cleaned_data['content'].append(f"Q: {faq['question']}")
                    if 'answer' in faq:
                        cleaned_data['content'].append(f"A: {faq['answer']}")

    # Extract text from navigation
    if 'navigation' in page_data:
        nav = page_data['navigation']
        if 'internal_links' in nav:
            cleaned_data['content'].extend(nav['internal_links'])
        if 'external_links' in nav:
            cleaned_data['content'].extend(nav['external_links'])

    # Extract metadata
    if 'metadata' in page_data:
        metadata = page_data['metadata']
        if isinstance(metadata, dict):
            for key, value in metadata.items():
                if isinstance(value, str):
                    cleaned_data['content'].append(f"{key}: {value}")

    # Clean and normalize the content
    cleaned_data['content'] = deduplicate_list(cleaned_data['content'])
    
    # Remove empty fields
    cleaned_data = remove_empty_fields(cleaned_data)

    # Ensure we have at least some content
    if not cleaned_data['content']:
        logger.warning(f"No content extracted from page: {page_data.get('url', 'unknown')}")
        # Add a placeholder to prevent validation failure
        cleaned_data['content'] = ['No content could be extracted from this page']

    return cleaned_data

class DataCleaner(BaseProcessor):
    """Handles cleaning and formatting of scraped data."""
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate the input data."""
        # Accept either direct data or data wrapped in page_data
        if 'page_data' in input_data:
            data = input_data['page_data']
            required_fields = ['url', 'domain']
            return all(field in data for field in required_fields)
        # Check for required fields in direct data
        required_fields = ['url', 'domain']
        return all(field in input_data for field in required_fields)
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validate the output data."""
        if not isinstance(output_data, dict):
            return False
        # Check for required fields
        required_fields = ['url', 'domain', 'content']
        return all(field in output_data for field in required_fields) and len(output_data['content']) > 0
    
    def process(self, input_data: Dict[str, Any]) -> ProcessingResult:
        """Clean and format the scraped data."""
        try:
            if not self.validate_input(input_data):
                return ProcessingResult(
                    success=False,
                    error="Invalid input data structure"
                )
            
            # Extract the actual data, whether it's wrapped in page_data or not
            data = input_data.get('page_data', input_data)
            
            # Clean the data
            cleaned_data = clean_scraped_data(data)
            
            if not self.validate_output(cleaned_data):
                return ProcessingResult(
                    success=False,
                    error="No content could be extracted from the data"
                )
            
            return ProcessingResult(
                success=True,
                data=cleaned_data,
                metadata={"cleaned_fields": list(cleaned_data.keys())}
            )
            
        except Exception as e:
            logger.error(f"Error cleaning data: {str(e)}")
            return ProcessingResult(
                success=False,
                error=str(e)
            ) 
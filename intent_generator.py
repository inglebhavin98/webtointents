from typing import List, Dict, Any
import numpy as np
from urllib.parse import urlparse
from collections import defaultdict
import json
from llm_processor import LLMProcessor
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class IntentGenerator:
    def __init__(self, llm_processor: LLMProcessor):
        print(f"*** IntentGenerator.__init__")
        self.llm_processor = llm_processor
        
    def create_url_hierarchy(self, urls: List[str]) -> Dict[str, Any]:
        print(f"*** IntentGenerator.create_url_hierarchy")
        """Create a hierarchy based on URL structure."""
        hierarchy = defaultdict(list)
        base_paths = set()
        
        for url in urls:
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            
            if len(path_parts) > 1:
                base_path = path_parts[0]
                base_paths.add(base_path)
                hierarchy[base_path].append(url)
            else:
                hierarchy['root'].append(url)
        
        return {
            'root': list(hierarchy['root']),
            'categories': {path: urls for path, urls in hierarchy.items() if path != 'root'}
        }
    
    def detect_intent_collisions(self, intents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        print(f"*** IntentGenerator.detect_intent_collisions")
        """Detect potential collisions between intents using LLM analysis."""
        collisions = []
        
        # Batch intents for efficient LLM processing
        for i, intent1 in enumerate(intents):
            batch_to_compare = intents[i+1:i+6]  # Process in small batches
            if not batch_to_compare:
                continue
                
            # Format intents for LLM analysis
            intent_data = {
                'base_intent': {
                    'name': intent1['primary_intent'],
                    'goals': intent1['user_goals'],
                    'questions': intent1['natural_questions']
                },
                'compare_intents': [
                    {
                        'name': intent2['primary_intent'],
                        'goals': intent2['user_goals'],
                        'questions': intent2['natural_questions']
                    }
                    for intent2 in batch_to_compare
                ]
            }
            
            # Use LLM to analyze intent similarities
            similar_intents = self.llm_processor.analyze_intent_similarity(intent_data)
            if similar_intents:
                collisions.extend(similar_intents)
        
        return collisions
    
    def generate_intent_hierarchy(self, crawled_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        print(f"*** IntentGenerator.generate_intent_hierarchy")
        """Generate a complete intent hierarchy from crawled data using only LLM."""
        logger.info("Generating intent hierarchy from crawled data...")
        
        if not crawled_data:
            logger.warning("No crawled data provided")
            return {
                "intents": {},
                "collisions": [],
                "metadata": {
                    "status": "empty",
                    "message": "No pages to analyze"
                }
            }
        
        # Create URL-based hierarchy
        urls = [data['url'] for data in crawled_data]
        url_hierarchy = self.create_url_hierarchy(urls)
        logger.info(f"Created URL hierarchy with {len(urls)} URLs")
        
        # Process each page for intents
        intents_by_category = defaultdict(list)
        all_intents = []
        
        for page_data in crawled_data:
            logger.info(f"Processing page: {page_data['url']}")
            
            # Get LLM-generated intents
            llm_results = self.llm_processor.process_page_for_intents(page_data)
            
            if llm_results:
                # Extract metadata
                metadata = page_data.get('metadata', {})
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except json.JSONDecodeError:
                        metadata = {}
                
                # Create intent structure
                intent = {
                'primary_intent': llm_results.get('primary_intent', ''),
                'user_goals': llm_results.get('user_goals', []),
                'natural_questions': llm_results.get('natural_questions', []),
                'bot_response': llm_results.get('bot_response', ''),
                'named_entities': llm_results.get('named_entities', []),
                'related_intents': llm_results.get('related_intents', []),
                'source_url': page_data.get('url', ''),
                'confidence_score': llm_results.get('confidence_score', 0.0),
                'page_title': metadata.get('title', 'Untitled Page'),
                'page_description': metadata.get('description', '')
            }
                
                # Add to appropriate category based on URL
                parsed_url = urlparse(page_data['url'])
                path_parts = parsed_url.path.strip('/').split('/')
                category = path_parts[0] if len(path_parts) > 1 else 'root'
                
                intents_by_category[category].append(intent)
                all_intents.append(intent)
        
        if not all_intents:
            logger.warning("No intents were generated from the crawled data")
            return {
                "intents": {},
                "collisions": [],
                "metadata": {
                    "status": "no_intents",
                    "message": "No intents could be generated from the crawled pages"
                }
            }
        
        logger.info(f"Processed {len(all_intents)} intents")
        
        # Detect collisions
        collisions = self.detect_intent_collisions(all_intents)
        logger.info(f"Found {len(collisions)} potential intent collisions")
        
        # Generate final hierarchy using LLM
        hierarchy_input = {
            'intents': all_intents,
            'url_structure': url_hierarchy,
            'collisions': collisions
        }
        
        final_hierarchy = self.llm_processor.generate_intent_hierarchy(hierarchy_input)
        
        # If LLM hierarchy generation fails, return a basic hierarchy
        if not final_hierarchy:
            logger.warning("LLM hierarchy generation failed, falling back to basic hierarchy")
            final_hierarchy = {
                "intents": intents_by_category,
                "collisions": collisions,
                "metadata": {
                    "status": "basic",
                    "message": "Using basic URL-based hierarchy due to LLM analysis failure"
                }
            }
        
        logger.info("Generated final intent hierarchy")
        return final_hierarchy
    
    def export_intents(self, hierarchy: Dict[str, Any], format: str = 'json') -> str:
        print(f"*** IntentGenerator.export_intents")
        """Export intents in the specified format."""
        if format == 'json':
            return json.dumps(hierarchy, indent=2)
        elif format == 'csv':
            # Create CSV format
            rows = []
            for category, data in hierarchy['hierarchy']['categories'].items():
                for intent in data['intents']:
                    row = {
                        'category': category,
                        'question': intent['question'],
                        'response': intent['response'],
                        'source_url': intent['source_url'],
                        'page_type': intent['page_type']
                    }
                    rows.append(row)
            
            if not rows:
                return "No intents to export"
                
            # Convert to CSV string
            import csv
            import io
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")

import json
from datetime import datetime
import os

class StorageHandler:
    def __init__(self):
        self.storage_dir = "crawl_results"
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def save_crawl_results(self, results, url):
        print(f"*** save_crawl_results")
        """Save crawl results to a JSON file."""

        if not results:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crawl_{timestamp}_{url.replace('https://', '').replace('/', '_')}.json"
        filepath = os.path.join(self.storage_dir, filename)
        
        # Group results by domain
        organized_results = {}
        for result in results:
            domain = result['domain']
            if domain not in organized_results:
                organized_results[domain] = {
                    'pages': [],
                    'total_pages': 0,
                    'unique_internal_links': set(),
                    'unique_external_links': set()
                }
            
            organized_results[domain]['pages'].append(result)
            organized_results[domain]['total_pages'] += 1
            organized_results[domain]['unique_internal_links'].update(result['navigation']['internal_links'])
            organized_results[domain]['unique_external_links'].update(result['navigation']['external_links'])
        
        # Convert sets to lists for JSON serialization
        for domain_data in organized_results.values():
            domain_data['unique_internal_links'] = list(domain_data['unique_internal_links'])
            domain_data['unique_external_links'] = list(domain_data['unique_external_links'])
        
        with open(filepath, 'w') as f:
            json.dump({
                'metadata': {
                    'crawl_date': datetime.now().isoformat(),
                    'total_domains': len(organized_results),
                    'total_pages': sum(d['total_pages'] for d in organized_results.values())
                },
                'domains': organized_results
            }, f, indent=2)
        return filename
    
    def get_crawl_results(self, filename):
        print(f"*** get_crawl_results")
        try:
            filepath = os.path.join(self.storage_dir, filename)
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return None
            
    def list_crawls(self):
        print(f"*** list_crawls")
        if not os.path.exists(self.storage_dir):
            return []
        return [f for f in os.listdir(self.storage_dir) if f.startswith('crawl_')]

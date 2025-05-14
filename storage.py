
import json
from datetime import datetime
import os

class StorageHandler:
    def __init__(self):
        self.storage_dir = "crawl_results"
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def save_crawl_results(self, results, url):
        if not results:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crawl_{timestamp}_{url.replace('https://', '').replace('/', '_')}.json"
        filepath = os.path.join(self.storage_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        return filename
    
    def get_crawl_results(self, filename):
        try:
            filepath = os.path.join(self.storage_dir, filename)
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return None
            
    def list_crawls(self):
        if not os.path.exists(self.storage_dir):
            return []
        return [f for f in os.listdir(self.storage_dir) if f.startswith('crawl_')]

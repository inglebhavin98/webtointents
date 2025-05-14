
from replit.object_storage import Client
import json
from datetime import datetime

class StorageHandler:
    def __init__(self):
        self.client = Client()
    
    def save_crawl_results(self, results, url):
        if not results:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crawl_{timestamp}_{url.replace('https://', '').replace('/', '_')}.json"
        
        self.client.upload_from_text(
            filename,
            json.dumps(results, indent=2)
        )
        return filename
    
    def get_crawl_results(self, filename):
        try:
            content = self.client.download_as_text(filename)
            return json.loads(content)
        except:
            return None
            
    def list_crawls(self):
        return [obj.name for obj in self.client.list() if obj.name.startswith('crawl_')]

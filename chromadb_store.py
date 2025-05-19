"""
ChromaDB storage module for cleaned web page data.
- Each document = one cleaned page (after clean_scraped_data)
- Uses sentence-transformers for embedding
- Stores flattened content and metadata for semantic search and filtering
"""
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import hashlib
import logging
import os
import json
import datetime

# Initialize embedding model (can be swapped for OpenAI if needed)
EMBED_MODEL_NAME = 'all-MiniLM-L6-v2'
_embedder = SentenceTransformer(EMBED_MODEL_NAME)

logger = logging.getLogger(__name__)

def get_embedding(text: str):
    try:
        embedding = _embedder.encode([text])[0]
        logger.info("[ChromaDB] Embedding generated successfully.")
        return embedding
    except Exception as e:
        logger.error(f"[ChromaDB] Embedding failed: {e}")
        raise

def flatten_content(cleaned_data: dict) -> str:
    """Flatten all relevant text fields into a single string for embedding."""
    parts = []
    for key in ['headers', 'faqs_clean', 'content']:
        val = cleaned_data.get(key)
        if isinstance(val, list):
            parts.extend([str(x) for x in val if x])
    # Flatten chunks (list of lists)
    chunks = cleaned_data.get('chunks')
    if isinstance(chunks, list):
        for chunk in chunks:
            if isinstance(chunk, list):
                parts.extend([str(x) for x in chunk if x])
    return '\n'.join(parts)

def initialize_chromadb_collection(collection_name: str = 'web_pages_cleaned', persist_dir: str = './chromadb_data'):
    """Initialize and return a persistent ChromaDB collection."""
    logger.info(f"[ChromaDB] Initializing client with persist_dir: {persist_dir}")
    client = chromadb.PersistentClient(path=persist_dir)
    if collection_name not in [c.name for c in client.list_collections()]:
        collection = client.create_collection(collection_name)
        logger.info(f"[ChromaDB] Created new collection: {collection_name}")
    else:
        collection = client.get_collection(collection_name)
        logger.info(f"[ChromaDB] Loaded existing collection: {collection_name}")
    return collection

def store_page_in_chromadb(cleaned_data: dict, url: str, collection=None):
    logger.info(f"[ChromaDB] Storing page: {url}")
    # Save cleaned data to a local JSON file before storing in ChromaDB
    os.makedirs('chromadb_cleaned_json', exist_ok=True)
    safe_url = url.replace('https://', '').replace('http://', '').replace('/', '_')
    filename = f"cleaned_{safe_url}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_path = os.path.join('chromadb_cleaned_json', filename)
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
    logger.info(f"[ChromaDB] Cleaned data saved to {save_path}")
    if collection is None:
        collection = initialize_chromadb_collection()
    client = getattr(collection, '_client', None)
    # Flatten content for embedding
    try:
        content_str = flatten_content(cleaned_data)
        logger.info("[ChromaDB] Content flattened for embedding.")
    except Exception as e:
        logger.error(f"[ChromaDB] Content flattening failed: {e}")
        raise
    try:
        embedding = get_embedding(content_str)
    except Exception as e:
        logger.error(f"[ChromaDB] Embedding step failed: {e}")
        raise
    # Prepare metadata
    meta = {
        'url': url,
        'title': cleaned_data.get('metadata', {}).get('title', ''),
        'description': cleaned_data.get('metadata', {}).get('description', ''),
        # Only store headers/faqs_clean as joined strings, not lists (ChromaDB metadata must be str/int/float/bool/None)
        'headers': '\n'.join(cleaned_data.get('headers', [])) if isinstance(cleaned_data.get('headers', []), list) else (cleaned_data.get('headers', '') or ''),
        'faqs_clean': '\n'.join(cleaned_data.get('faqs_clean', [])) if isinstance(cleaned_data.get('faqs_clean', []), list) else (cleaned_data.get('faqs_clean', '') or ''),
        'domain': url.split('/')[2] if '://' in url else url,
    }
    try:
        collection.upsert(
            ids=[url],
            embeddings=[embedding],
            documents=[content_str],
            metadatas=[meta]
        )
        logger.info(f"[ChromaDB] Upserted page: {url}")
    except Exception as e:
        logger.error(f"[ChromaDB] Upsert failed: {e}")
        raise
    # Force persist to disk if possible
    if client and hasattr(client, 'persist'):
        try:
            client.persist()
            logger.info(f"[ChromaDB] Persisted to disk at: {getattr(client, 'settings', {}).get('persist_directory', 'unknown')}")
        except Exception as e:
            logger.error(f"[ChromaDB] Persist failed: {e}")
    return True

# Example usage:
# collection = initialize_chromadb_collection()
# store_page_in_chromadb(cleaned_data, url, collection)

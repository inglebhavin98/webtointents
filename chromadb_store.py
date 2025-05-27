import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import os
from sentence_transformers import SentenceTransformer

# --- ChromaDB utility functions for persistent client and collection management ---
def get_chromadb_client():
    """Return a persistent ChromaDB client (singleton pattern)."""
    chroma_dir = os.path.join(os.path.dirname(__file__), 'chroma_db_store')
    return chromadb.PersistentClient(path=chroma_dir)

def get_or_create_cleaned_collection(client=None):
    print(f"*** get_or_create_cleaned_collection")
    """Get or create the 'cleaned_pages' collection."""
    if client is None:
        client = get_chromadb_client()
    collection = client.get_or_create_collection(
        name="cleaned_pages",
        metadata={"description": "Cleaned and embedded web pages, URL as ID"}
    )
    return collection

def get_or_create_intents_collection(client=None):
    print(f"*** get_or_create_intents_collection")
    """Get or create the 'intents' collection for storing intent analysis results."""
    if client is None:
        client = get_chromadb_client()
    collection = client.get_or_create_collection(
        name="intents",
        metadata={"description": "LLM-generated intent analysis results, keyed by document or chunk ID"}
    )
    return collection

def query_similar_pages(query_text, n_results=5):
    print(f"*** query_similar_pages")
    """Query ChromaDB for similar pages to the input text."""
    client = get_chromadb_client()
    collection = get_or_create_cleaned_collection(client)
    embedding = embed_text(query_text)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results
    )
    return results

# Initialize ChromaDB persistent client and collection
CHROMA_DIR = os.path.join(os.path.dirname(__file__), 'chroma_db_store')
client = chromadb.PersistentClient(path=CHROMA_DIR)
COLLECTION_NAME = "cleaned_pages"
collection = client.get_or_create_collection(COLLECTION_NAME)

# --- Embedding model setup (free, local) ---
MODEL = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dims, free, local

def get_page_text_for_embedding(page_data):
    print(f"*** get_page_text_for_embedding")
    # Concatenate all relevant text fields for embedding
    texts = []
    prioritized_keys = ["chunks", "content", "headers", "faqs_clean"]
    for key in prioritized_keys:
        if key in page_data:
            val = page_data[key]
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, dict) and 'text' in item:
                        texts.append(item['text'])
                    elif isinstance(item, str):
                        texts.append(item)
            elif isinstance(val, str):
                texts.append(val)
    # Fallback: if still empty, extract all string values recursively
    if not any(t.strip() for t in texts):
        def extract_all_strings(obj):
            print(f"*** extract_all_strings")
            found = []
            if isinstance(obj, dict):
                for v in obj.values():
                    found.extend(extract_all_strings(v))
            elif isinstance(obj, list):
                for item in obj:
                    found.extend(extract_all_strings(item))
            elif isinstance(obj, str) and obj.strip():
                found.append(obj.strip())
            return found
        texts = extract_all_strings(page_data)
    return "\n".join([t for t in texts if t.strip()])

def embed_text(text):
    print(f"*** embed_text")
    # Use SentenceTransformer to get embedding (free, local)
    return MODEL.encode(text).tolist()

def upsert_cleaned_page(url, page_data):
    print(f"*** upsert_cleaned_page")
    text = get_page_text_for_embedding(page_data)
    if not text.strip():
        raise ValueError("No text found for embedding.")
    embedding = embed_text(text)
    # Store in ChromaDB with url as ID
    collection.upsert(
        ids=[url],
        embeddings=[embedding],
        documents=[text],
        metadatas=[{"source": url}]
    )
    # No need to call client.persist() with PersistentClient
    return True

import chromadb
from sentence_transformers import SentenceTransformer
import os

# Set up ChromaDB persistent client and collection
CHROMA_DIR = os.path.join(os.path.dirname(__file__), 'chroma_db_store')
client = chromadb.PersistentClient(path=CHROMA_DIR)
COLLECTION_NAME = "cleaned_pages"
collection = client.get_or_create_collection(COLLECTION_NAME)

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Query text
query_text = "something for seniors?"
query_embedding = model.encode(query_text).tolist()

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3,
    include=["documents", "metadatas", "distances"]
)

for i in range(len(results['documents'][0])):
    print(f"Result #{i+1}")
    print("ID:", results['ids'][0][i])
    # Try to print URL from metadata if available, else fallback to ID
    url = results['metadatas'][0][i].get('source') if results['metadatas'][0][i] else None
    print("URL:", url if url else results['ids'][0][i])
    # print("Text:", results['documents'][0][i])
    # print("Metadata:", results['metadatas'][0][i])
    print("Distance:", results['distances'][0][i])
    print("-" * 30)

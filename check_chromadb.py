import sys
import chromadb_store

if len(sys.argv) < 2:
    print("Usage: python check_chromadb.py <url>")
    sys.exit(1)

url = sys.argv[1]
collection = chromadb_store.initialize_chromadb_collection()
print("All IDs in collection:", collection.get()["ids"])
result = collection.get(ids=[url])

if result['ids']:
    print(f"Found in ChromaDB: {result['ids']}")
else:
    print("Not found in ChromaDB.")

print(f"Documents: {result.get('documents', [])}")
print(f"Metadatas: {result.get('metadatas', [])}")
print(f"Embeddings: {result.get('embeddings', [])}")
print(f"Result keys: {list(result.keys())}")
print(f"Full result: {result}")

from chromadb_store import get_chromadb_client, get_or_create_cleaned_collection
import json

if __name__ == "__main__":
    client = get_chromadb_client()
    collection = get_or_create_cleaned_collection(client)
    # Get all IDs in the collection
    ids = collection.get()['ids']
    print(f"Found {len(ids)} documents in ChromaDB.")
    # Fetch all documents, embeddings, and metadata
    all_data = collection.get(include=['embeddings', 'documents', 'metadatas'])
    for i, doc_id in enumerate(all_data['ids']):
        print(f"\n--- Document {i+1} ---")
        print(f"ID (URL): {doc_id}")
        print(f"Metadata: {json.dumps(all_data['metadatas'][i], indent=2)}")
        print(f"Document (text): {all_data['documents'][i][:500]}{'...' if len(all_data['documents'][i]) > 500 else ''}")
        print(f"Embedding (first 10 dims): {all_data['embeddings'][i][:10]}")
        print(f"Embedding (length): {len(all_data['embeddings'][i])}")

import streamlit as st
from chromadb_store import get_chromadb_client, get_or_create_cleaned_collection, get_or_create_intents_collection
from llm_processor import LLMProcessor
import json

def dashboard_route():
    st.title("Web Pages Dashboard")
    client = get_chromadb_client()
    web_pages_collection = get_or_create_cleaned_collection(client)
    intents_collection = get_or_create_intents_collection(client)

    # 1. Show total number of URLs/pages
    web_pages = web_pages_collection.get(include=["metadatas", "documents"])
    ids = web_pages.get("ids", [])
    st.metric("Total Pages in web_pages Collection", len(ids))

    # 2. CTA: Process for Intents
    if st.button("Process for Intents"):
        st.info("Processing all pages for intent extraction. This may take a while...")
        llm = LLMProcessor()
        processed_count = 0
        for i, doc_id in enumerate(ids):
            doc = web_pages["documents"][i] if web_pages["documents"] and i < len(web_pages["documents"]) else None
            meta = web_pages["metadatas"][i] if web_pages["metadatas"] and i < len(web_pages["metadatas"]) else {}
            url = meta.get("source", doc_id)
            if not doc:
                continue
            # Call LLM for intent extraction (prompt to be provided by user later)
            # For now, use llm.generate_intent(doc) as placeholder
            intent_result = llm.generate_intent(doc)
            # Store in intents collection
            intents_collection.add(
                documents=[json.dumps(intent_result)],
                metadatas=[{"url": url}],
                ids=[doc_id]
            )
            processed_count += 1
        st.success(f"Processed {processed_count} pages for intents and stored results.")

    # --- Intents ChromaDB Tab ---
    st.markdown("---")
    from intents_chromadb_tab import show_intents_chromadb_tab
    show_intents_chromadb_tab()

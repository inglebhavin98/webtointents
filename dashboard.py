import streamlit as st
from chromadb_store import get_chromadb_client, get_or_create_cleaned_collection, get_or_create_intents_collection
from llm_processor import LLMProcessor
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import asyncio
import time

INTENT_EXTRACTION_PROMPT = '''You are an expert conversation designer helping analyze a website for contact center transformation.

Below is content from a single webpage. Your task is to identify the top 10 most probable user intents based on the content.

Output only a clean list of intents — each should be short, clear, and action-oriented.

---

[CONTENT START]
{{cleaned_content}}
[CONTENT END]

---

Please list the 10 most probable user intents found in this content.
Do not add explanations or formatting — just output a plain numbered list.'''

def call_llm_for_intents(llm, cleaned_content):
    print(f"*** Calling LLM for intents with content: {cleaned_content[:50]}...")  # Debugging line
    prompt = INTENT_EXTRACTION_PROMPT.replace("{{cleaned_content}}", cleaned_content)
    response = llm.generate_intent(prompt)
    # Parse numbered list into a Python list
    if response:
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        numbered = [l for l in lines if l[0].isdigit() and '.' in l]
        if numbered:
            return [l.split('.', 1)[1].strip() for l in numbered]
        return lines
    return []

async def async_generate_intent(llm, cleaned_content):
    print(f"*** Async generating intent for content")  # Debugging line
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, call_llm_for_intents, llm, cleaned_content)
    await asyncio.sleep(6)  # Add delay to avoid rate limit
    return result

def cluster_and_summarize_intents_llm(intents_collection):
    print(f"*** Clustering and summarizing intents")  # Debugging line
    # 1. Extract all intents from the intents collection
    results = intents_collection.get(include=["documents", "metadatas"])
    docs = results.get("documents", [])
    all_intents = []
    for doc in docs:
        try:
            # Each doc is a list of intents (from call_llm_for_intents)
            intent_list = json.loads(doc) if isinstance(doc, str) else doc
            # Flatten: if intent_list is a list, add all; if string, add as one
            if isinstance(intent_list, list):
                all_intents.extend([i for i in intent_list if isinstance(i, str)])
            elif isinstance(intent_list, str):
                all_intents.append(intent_list)
        except Exception:
            continue
    # DEBUG: Show what was extracted
    if not all_intents:
        st.warning(f"No intents extracted from ChromaDB. Example doc: {docs[0] if docs else 'None'}")
        return []
    # 2. Use LLM to cluster and summarize
    llm = LLMProcessor()
    prompt = f"""You are an expert at clustering and summarizing user intents for contact center transformation.

Here is a list of user intents (may contain duplicates, paraphrases, or similar actions):

{all_intents}

Cluster these intents into groups of similar meaning. For each group, provide:
- The canonical intent (short, action-oriented)
- The frequency (number of times this intent or its variants appear)
- 2-3 sample variants from the group

Output as a markdown table with columns: Grouped Intent | Frequency | Sample Variants
"""
    response = llm.generate_intent(prompt)
    return response

def dashboard_route():
    print(f"*** Dashboard route")  # Debugging line
    st.title("Web Pages Dashboard")
    client = get_chromadb_client()
    web_pages_collection = get_or_create_cleaned_collection(client)
    intents_collection = get_or_create_intents_collection(client)

    # 1. Show total number of URLs/pages
    web_pages = web_pages_collection.get(include=["metadatas", "documents"])
    ids = web_pages.get("ids", [])
    st.metric("Total Pages in web_pages Collection", len(ids))

    # 2. CTA: Process for Intents (async batch)
    if st.button("Process for Intents"):
        st.info("Processing all pages for intent extraction. This may take a while...")
        llm = LLMProcessor()
        processed_count = 0
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = []
        # Limit to 5 pages for testing
        max_pages = 5
        for i, doc_id in enumerate(ids[:max_pages]):
            doc = web_pages["documents"][i] if web_pages["documents"] and i < len(web_pages["documents"]) else None
            meta = web_pages["metadatas"][i] if web_pages["metadatas"] and i < len(web_pages["metadatas"]) else {}
            url = meta.get("source", doc_id)
            if not doc:
                continue
            tasks.append(async_generate_intent(llm, doc))
        results = []
        with st.spinner("Batch extracting intents with LLM..."):
            for f in asyncio.as_completed(tasks):
                result = loop.run_until_complete(f)
                results.append(result)
                processed_count += 1
                st.info(f"Processed {processed_count}/{len(tasks)}")
        for i, intent_result in enumerate(results):
            doc_id = ids[i]
            meta = web_pages["metadatas"][i] if web_pages["metadatas"] and i < len(web_pages["metadatas"]) else {}
            url = meta.get("source", doc_id)
            intents_collection.add(
                documents=[json.dumps(intent_result)],
                metadatas=[{"url": url}],
                ids=[doc_id]
            )
        st.success(f"Processed {processed_count} pages for intents and stored results.")

    # 3. Clustering and Frequency Summary
    st.header("Intent Clustering & Frequency Summary")
    summary_md = cluster_and_summarize_intents_llm(intents_collection)
    if summary_md:
        st.markdown(summary_md)
    else:
        st.info("No intents found to cluster.")

    # --- Intents ChromaDB Tab ---
    st.markdown("---")
    from intents_chromadb_tab import show_intents_chromadb_tab
    show_intents_chromadb_tab()

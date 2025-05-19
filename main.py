import streamlit as st
import logging
from crawler import WebsiteCrawler
from llm_processor import LLMProcessor
from intent_generator import IntentGenerator
import json
import os
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
from io import StringIO
from typing import Dict, Any
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def initialize_components():
    """Initialize all required components with proper error handling."""
    try:
        logger.info("Initializing components...")
        llm_processor = LLMProcessor()
        intent_generator = IntentGenerator(llm_processor)
        logger.info("All components initialized successfully")
        return llm_processor, intent_generator
    except Exception as e:
        logger.error(f"Error initializing components: {str(e)}")
        st.error(f"Error initializing components: {str(e)}")
        return None, None

def parse_uploaded_sitemap(uploaded_file):
    """Parse an uploaded sitemap XML file and return list of URLs."""
    try:
        content = uploaded_file.getvalue().decode('utf-8')
        tree = ET.parse(StringIO(content))
        root = tree.getroot()
        
        # Handle different sitemap formats
        namespace = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
        urls = []
        
        # Try with namespace first
        locs = root.findall(f'.//{namespace}loc')
        if not locs:
            # Try without namespace
            locs = root.findall('.//loc')
        
        urls = [loc.text for loc in locs]
        logger.info(f"Successfully parsed {len(urls)} URLs from sitemap")
        return urls
    except Exception as e:
        logger.error(f"Error parsing sitemap: {str(e)}")
        st.error(f"Error parsing sitemap: {str(e)}")
        return []

def display_intent_analysis(intent: Dict[str, Any]):
    """Display intent analysis in a structured format."""
    try:
        # Page Information
        st.subheader("Page Information")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Page Title", intent.get('page_title', 'N/A'))
        with col2:
            st.metric("Intent ID", intent.get('intent_id', 'N/A'))
        
        # Intent Analysis
        st.subheader("Intent Analysis")
        if isinstance(intent.get('primary_intent'), dict):
            # New format
            primary_intent = intent['primary_intent']
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Primary Intent", primary_intent.get('name', 'N/A'))
            with col2:
                st.metric("Confidence Score", f"{primary_intent.get('confidence', 0):.2f}")
            st.write("Description:", primary_intent.get('description', 'N/A'))
        else:
            # Legacy format
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Detected Intent", intent.get('primary_intent', 'N/A'))
            with col2:
                st.metric("Confidence Score", f"{intent.get('confidence_score', 0):.2f}")
        
        # User Goals
        st.subheader("User Goals")
        for goal in intent.get('user_goals', []):
            if isinstance(goal, dict):
                st.write(f"• {goal['goal']}")
                with st.expander("Details"):
                    st.write("Steps:")
                    for step in goal.get('steps', []):
                        st.write(f"  - {step}")
                    if goal.get('blockers'):
                        st.write("Potential Blockers:")
                        for blocker in goal['blockers']:
                            st.write(f"  - {blocker}")
            else:
                st.write(f"• {goal}")
        
        # Questions and Answers
        st.subheader("Questions and Answers")
        for qa in intent.get('questions_and_answers', []):
            with st.expander(qa['question']):
                st.write("Answer:", qa['answer'])
                if qa.get('variations'):
                    st.write("Similar Questions:")
                    for var in qa['variations']:
                        st.write(f"- {var}")
        
        # Named Entities
        st.subheader("Named Entities")
        for entity in intent.get('named_entities', []):
            if isinstance(entity, dict):
                st.write(f"• {entity['type']}: {entity['value']}")
                if entity.get('context'):
                    st.write(f"  Context: {entity['context']}")
            else:
                st.write(f"• {entity}")
        
        # Topic Hierarchy
        if 'topic_hierarchy' in intent:
            st.subheader("Topic Analysis")
            topic = intent['topic_hierarchy']
            st.write(f"Main Topic: {topic['main_topic']}")
            st.write("Subtopics:")
            for sub in topic['subtopics']:
                st.write(f"- {sub}")
            st.write("Keywords:")
            for kw in topic['keywords']:
                st.write(f"- {kw}")
        
        # Intent Relationships
        if 'intent_relationships' in intent:
            st.subheader("Intent Relationships")
            rels = intent['intent_relationships']
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"Parent Intent: {rels['parent_intent']}")
            with col2:
                if rels.get('related_intents'):
                    st.write("Related Intents:", ", ".join(rels['related_intents']))
            if rels.get('child_intents'):
                st.write("More Specific Intents:")
                for child in rels['child_intents']:
                    st.write(f"- {child}")
        elif 'related_intents' in intent:
            st.subheader("Related Intents")
            st.write(", ".join(intent['related_intents']))
        
        # Suggested Response
        if 'suggested_responses' in intent:
            st.subheader("Suggested Responses")
            for resp in intent['suggested_responses']:
                with st.expander(f"Response for: {resp['trigger']}"):
                    st.write(resp['response'])
                    if resp.get('followup_questions'):
                        st.write("Follow-up Questions:")
                        for q in resp['followup_questions']:
                            st.write(f"- {q}")
        elif 'bot_response' in intent:
            st.subheader("Bot Response")
            st.write(intent['bot_response'])
        
        # Analysis Metadata
        if 'metadata' in intent:
            st.subheader("Content Analysis")
            meta = intent['metadata']
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Quality Score", f"{meta['content_quality_score']:.2f}")
            with col2:
                st.metric("Technical Level", meta['technical_complexity'])
            with col3:
                st.metric("Content Type", meta['action_orientation'])
            
    except Exception as e:
        st.error(f"Error displaying intent analysis: {str(e)}")

def display_contact_center_intent_map(intent_map: dict):
    """Display the specialized contact center intent map in a readable format."""
    if not intent_map:
        st.error("No intent map data to display.")
        return

    # 1. High-Level Summary
    st.header("High-Level Summary")
    summary = intent_map.get("high_level_summary", {})
    st.write(f"**Offering:** {summary.get('offering', 'N/A')}")
    st.write(f"**Target Audience:** {summary.get('target_audience', 'N/A')}")

    # 2. Core User Intents
    st.header("Core User Intents")
    for intent in intent_map.get("core_intents", []):
        st.subheader(f"{intent.get('intent_name', 'Unnamed Intent')}")
        st.write(f"**Priority:** {intent.get('priority', 'N/A')}")
        st.write("**Signals:**")
        for signal in intent.get("signals", []):
            st.write(f"- *{signal.get('type', 'N/A')}:* {signal.get('content', '')} (Confidence: {signal.get('confidence', 'N/A')})")

    # 3. Feature to Intent Mapping Table
    st.header("Feature to Intent Mapping")
    mapping = intent_map.get("feature_intent_mapping", [])
    if mapping:
        import pandas as pd
        df = pd.DataFrame(mapping)
        st.table(df)
    else:
        st.info("No feature to intent mapping available.")

    # 4. Sub-Intents (Optional)
    if intent_map.get("sub_intents"):
        st.header("Sub-Intents")
        for sub in intent_map["sub_intents"]:
            st.subheader(f"Parent Intent: {sub.get('parent_intent', 'N/A')}")
            for child in sub.get('children', []):
                st.write(f"- **{child.get('name', 'N/A')}**: {child.get('motivation', '')}")
                if child.get('signals'):
                    st.write("  Signals:")
                    for sig in child['signals']:
                        st.write(f"    - {sig}")

    # 5. Internal Link Clustering (Optional)
    if intent_map.get("link_clusters"):
        st.header("Internal Link Clusters")
        for cluster in intent_map["link_clusters"]:
            st.subheader(cluster.get('cluster_name', 'Unnamed Cluster'))
            st.write(f"Pattern: {cluster.get('pattern', '')}")
            st.write("Links:")
            for url in cluster.get('urls', []):
                st.write(f"- {url}")

def clean_scraped_data(page_data: dict) -> dict:
    """Clean and preprocess scraped page data before LLM analysis."""
    import re
    from collections import OrderedDict

    def deduplicate_list(items):
        seen = set()
        deduped = []
        for item in items:
            key = item.strip().lower()
            if key and key not in seen:
                deduped.append(item)
                seen.add(key)
        return deduped

    def remove_empty_fields(d):
        if isinstance(d, dict):
            return {k: remove_empty_fields(v) for k, v in d.items() if v not in [None, '', [], {}]}
        elif isinstance(d, list):
            return [remove_empty_fields(x) for x in d if x not in [None, '', [], {}]]
        else:
            return d

    def chunk_by_headers(content_blocks):
        # Simple chunking by h2/h3 or paragraph blocks
        chunks = []
        current = []
        for block in content_blocks:
            if isinstance(block, dict) and block.get('tag') in ['h2', 'h3']:
                if current:
                    chunks.append(current)
                current = [block]
            else:
                current.append(block)
        if current:
            chunks.append(current)
        return chunks

    def normalize_text(text):
        # Remove CTAs (simple heuristics)
        cta_patterns = [r'click here', r'contact us', r'learn more', r'sign up', r'get started']
        for pat in cta_patterns:
            text = re.sub(pat, '', text, flags=re.IGNORECASE)
        # Expand common acronyms (add more as needed)
        acronyms = {'FAQ': 'Frequently Asked Questions', 'CTA': 'Call To Action'}
        for acro, full in acronyms.items():
            text = re.sub(rf'\b{acro}\b', full, text)
        return text.strip()

    # 1. Deduplicate headers, FAQs, repeated text
    if 'headers' in page_data:
        page_data['headers'] = deduplicate_list(page_data['headers'])
    if 'faqs' in page_data:
        page_data['faqs'] = deduplicate_list(page_data['faqs'])
    if 'content' in page_data and isinstance(page_data['content'], list):
        seen = set()
        deduped_content = []
        for block in page_data['content']:
            txt = block.get('text', '').strip().lower() if isinstance(block, dict) else str(block).strip().lower()
            if txt and txt not in seen:
                deduped_content.append(block)
                seen.add(txt)
        page_data['content'] = deduped_content

    # 2. Remove empty/missing fields
    page_data = remove_empty_fields(page_data)

    # 3. Chunk content by h2/h3 or paragraph block
    if 'content' in page_data and isinstance(page_data['content'], list):
        page_data['chunks'] = chunk_by_headers(page_data['content'])

    # 4. Keep clean FAQ dataset
    if 'faqs' in page_data:
        page_data['faqs_clean'] = [normalize_text(faq) for faq in page_data['faqs']]

    # 5. Normalize noisy text
    for key in ['headers', 'faqs_clean']:
        if key in page_data:
            page_data[key] = [normalize_text(t) for t in page_data[key]]
    if 'content' in page_data and isinstance(page_data['content'], list):
        for block in page_data['content']:
            if isinstance(block, dict) and 'text' in block:
                block['text'] = normalize_text(block['text'])

    # 6. Optionally tag chunks with metadata
    if 'chunks' in page_data:
        for i, chunk in enumerate(page_data['chunks']):
            for block in chunk:
                if isinstance(block, dict):
                    block['chunk_id'] = i

    return page_data

def main():
    # st.write(':green-background[App loaded! If you see this, the UI is rendering and waiting for your input.]')
    st.title("Intent Scraper")
    
    # Initialize components
    crawler = WebsiteCrawler()
    llm_processor, intent_generator = initialize_components()
    if not all([llm_processor, intent_generator]):
        st.error("Failed to initialize required components. Please check the logs for details.")
        return
    
    # Initialize session state
    if 'analyzed_intents' not in st.session_state:
        st.session_state.analyzed_intents = []
    if 'parsed_urls' not in st.session_state:
        st.session_state.parsed_urls = []
    
    # URL input and sitemap upload interface
    url_input = st.text_input("Enter URL(s) to analyze (comma-separated for batch)")
    uploaded_file = st.file_uploader("Or upload a sitemap", type=['xml'])

    # Parse multi-URL input
    urls = []
    # If sitemap is uploaded and parsed, override url_input and urls
    sitemap_urls = []
    if uploaded_file and st.button("Parse Sitemap"):
        sitemap_urls = parse_uploaded_sitemap(uploaded_file)
        if sitemap_urls:
            st.success(f"Successfully parsed {len(sitemap_urls)} URLs from sitemap")
            # Feed sitemap URLs to the comma-separated logic
            url_input = ', '.join(sitemap_urls)
            # Save to session state for Start Analysis
            st.session_state.sitemap_urls = sitemap_urls
    # If sitemap URLs were parsed, show them in a text area for review/edit
    if 'sitemap_urls' in st.session_state and st.session_state.sitemap_urls:
        url_input = st.text_area("Sitemap URLs (edit if needed, comma-separated)", value=', '.join(st.session_state.sitemap_urls), height=150)
        urls = [u.strip() for u in url_input.split(',') if u.strip()]
    elif url_input:
        urls = [u.strip() for u in url_input.split(',') if u.strip()]

    # Display URL selection if URLs are parsed
    if st.session_state.parsed_urls:
        st.subheader("Select URLs to Analyze")
        selected_urls = st.multiselect(
            "Choose URLs to analyze",
            st.session_state.parsed_urls,
            default=st.session_state.parsed_urls[:5]  # Default to first 5 URLs
        )
        st.write(f"Selected {len(selected_urls)} URLs for analysis")
    else:
        selected_urls = []

    if st.button("Start Analysis"):
        # Use batch URLs if provided, else use selected_urls from sitemap
        urls_to_process = urls if urls else selected_urls
        if not urls_to_process and 'sitemap_urls' in st.session_state and st.session_state.sitemap_urls:
            urls_to_process = st.session_state.sitemap_urls
        if urls_to_process:
            stop_crawl = False
            stop_button_placeholder = st.empty()
            # Show stop button before crawling loop starts
            def stop_crawl_callback():
                st.session_state.stop_crawl = True
            stop_button_placeholder.button("Stop Crawling", on_click=stop_crawl_callback, key="stop_crawling_main")
            with st.spinner("Crawling pages..."):
                pages = {}
                progress_bar = st.progress(0)
                for i, url in enumerate(urls_to_process):
                    # Check for stop signal
                    if 'stop_crawl' in st.session_state and st.session_state.stop_crawl:
                        st.warning("Crawling stopped by user.")
                        break
                    try:
                        logger.info(f"Crawling URL: {url}")
                        with st.spinner(f"Crawling {url}..."):
                            page_data = crawler.crawl_url(url)
                            if page_data:
                                # Clean immediately
                                cleaned = clean_scraped_data(page_data)
                                # Store in ChromaDB immediately
                                try:
                                    from chromadb_store import upsert_cleaned_page
                                    upsert_cleaned_page(url, cleaned)
                                except Exception as e:
                                    st.warning(f"ChromaDB storage failed for {url}: {str(e)}")
                                pages[url] = page_data
                                # Also accumulate cleaned_pages for preview
                                if 'cleaned_pages' not in locals():
                                    cleaned_pages = {}
                                cleaned_pages[url] = cleaned
                        progress_bar.progress((i + 1) / len(urls_to_process))
                    except Exception as e:
                        logger.error(f"Error crawling {url}: {str(e)}")
                        continue
                # Remove stop button and reset state
                stop_button_placeholder.empty()  # This hides the button after crawling ends
                if 'stop_crawl' in st.session_state:
                    del st.session_state.stop_crawl
                if pages:
                    st.session_state.pages = pages
                    st.session_state.cleaned_pages = cleaned_pages if 'cleaned_pages' in locals() else None
                    st.session_state.show_cleaned = True
                    st.success(f"Successfully crawled and processed {len(pages)} pages")
                    # --- Automatically move to Clean Scraped Data step ---
                    import datetime
                    import hashlib
                    import os
                    cleaned_pages = {}
                    os.makedirs('crawl_results', exist_ok=True)
                    for page_url, page_data in st.session_state.pages.items():
                        cleaned = clean_scraped_data(page_data)
                        cleaned_pages[page_url] = cleaned
                        # Save cleaned data to JSON file
                        safe_url = page_url.replace('https://', '').replace('http://', '').replace('/', '_')
                        url_hash = hashlib.md5(page_url.encode('utf-8')).hexdigest()
                        filename = f"cleaned_{safe_url}_{url_hash}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        save_path = os.path.join('crawl_results', filename)
                        with open(save_path, 'w', encoding='utf-8') as f:
                            import json
                            json.dump(cleaned, f, indent=2, ensure_ascii=False)
                        # Store in ChromaDB
                        try:
                            from chromadb_store import upsert_cleaned_page
                            upsert_cleaned_page(page_url, cleaned)
                        except Exception as e:
                            st.warning(f"ChromaDB storage failed for {page_url}: {str(e)}")
                    st.session_state.cleaned_pages = cleaned_pages
                    st.session_state.show_cleaned = True
            # Show stop button while crawling
            def stop_crawl_callback():
                st.session_state.stop_crawl = True
            stop_button_placeholder.button("Stop Crawling", on_click=stop_crawl_callback)

    # Show cleaning CTA and previews if pages are in session state
    if 'pages' in st.session_state and st.session_state.pages:
        # Clean Scraped Data button
        # DO NOT DELETE
        # if st.button("Clean Scraped Data"):
        #     import datetime
        #     import hashlib
        #     import os
        #     cleaned_pages = {}
        #     os.makedirs('crawl_results', exist_ok=True)
        #     for page_url, page_data in st.session_state.pages.items():
        #         cleaned = clean_scraped_data(page_data)
        #         cleaned_pages[page_url] = cleaned
        #         # Save cleaned data to JSON file
        #         safe_url = page_url.replace('https://', '').replace('http://', '').replace('/', '_')
        #         url_hash = hashlib.md5(page_url.encode('utf-8')).hexdigest()
        #         filename = f"cleaned_{safe_url}_{url_hash}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        #         save_path = os.path.join('crawl_results', filename)
        #         with open(save_path, 'w', encoding='utf-8') as f:
        #             import json
        #             json.dump(cleaned, f, indent=2, ensure_ascii=False)
        #         # Store in ChromaDB
        #         try:
        #             from chromadb_store import upsert_cleaned_page
        #             upsert_cleaned_page(page_url, cleaned)
        #         except Exception as e:
        #             st.warning(f"ChromaDB storage failed for {page_url}: {str(e)}")
        #     st.session_state.cleaned_pages = cleaned_pages
        #     st.session_state.show_cleaned = True
        # DO NOT DELETE END

        # Show cleaned or raw preview based on state
        if st.session_state.get('show_cleaned') and st.session_state.get('cleaned_pages'):
            # st.header("Cleaned Scraped Data Preview")
            # DO NOT DELETE
            # for page_url, page_data in st.session_state.cleaned_pages.items():
            #     with st.expander(f"{page_url}"):
            #         st.write("**Metadata:**")
            #         st.json(page_data.get('metadata', {}))
            #         st.write("**Structure:**")
            #         st.json(page_data.get('structure', {}))
            #         st.write("**Navigation:**")
            #         st.json(page_data.get('navigation', {}))
            #         import json
            #         import hashlib
            #         raw_json = json.dumps(page_data, indent=2, ensure_ascii=False)
            #         url_hash = hashlib.md5(page_url.encode('utf-8')).hexdigest()
            #         col1, col2 = st.columns(2)
            #         with col1:
            #             if st.button(f"Save JSON", key=f"save_json_{url_hash}_cleaned_{page_url}"):
            #                 import datetime
            #                 import os
            #                 safe_url = page_url.replace('https://', '').replace('http://', '').replace('/', '_')
            #                 filename = f"scraped_{safe_url}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            #                 save_path = os.path.join('crawl_results', filename)
            #                 os.makedirs('crawl_results', exist_ok=True)
            #                 with open(save_path, 'w', encoding='utf-8') as f:
            #                     f.write(raw_json)
            #                 st.success(f"Saved to {save_path}")
            #         with col2:
            #             st.code(raw_json, language='json')
            #             st.caption("You can copy the above JSON using the copy button in the code block.")

            # --- LLM Intent Extraction Section (now below the cleaned data preview) ---
            # DO NOT DELETE END
            st.markdown("---")
            # DO NOT DELETE START
            # st.subheader("LLM Intent Extraction")
            # for page_url, page_data in st.session_state.cleaned_pages.items():
            #     url_hash = hashlib.md5(page_url.encode('utf-8')).hexdigest()
            #     st.markdown(f"**Page:** {page_url}")

            #     def extract_all_text(data, prioritized_keys=None):
            #         # Recursively extract all non-empty text from prioritized fields, fallback to all text
            #         if prioritized_keys is None:
            #             prioritized_keys = ['chunks', 'content', 'headers', 'faqs_clean']
            #         texts = []
            #         def _extract(obj):
            #             if isinstance(obj, dict):
            #                 for k, v in obj.items():
            #                     if k in prioritized_keys:
            #                         _extract(v)
            #                     elif isinstance(v, (dict, list)):
            #                         _extract(v)
            #                     elif isinstance(v, str) and v.strip():
            #                         texts.append(v.strip())
            #             elif isinstance(obj, list):
            #                 for item in obj:
            #                     _extract(item)
            #             elif isinstance(obj, str) and obj.strip():
            #                 texts.append(obj.strip())
            #         # First try prioritized keys
            #         for key in prioritized_keys:
            #             if key in data:
            #                 _extract(data[key])
            #         # If still empty, fallback to all text in the structure
            #         if not texts:
            #             _extract(data)
            #         return '\n'.join(texts)

            #     cleaned_text = extract_all_text(page_data)

            #     with st.expander(f"Show cleaned text sent to LLM for {page_url}", expanded=False):
            #         st.write("--- Cleaned Data Structure ---")
            #         st.json(page_data)
            #         st.write("--- Cleaned Text Sent to LLM ---")
            #         st.write(cleaned_text if cleaned_text else "(No text found)")
            #     llm_btn = st.button(f"Extract Intents with LLM", key=f"llm_extract_{url_hash}_{page_url}")
            #     if llm_btn:
            #         if not cleaned_text:
            #             st.warning("No cleaned text found for this page. Cannot extract intents.")
            #         else:
            #             try:
            #                 llm_result = llm_processor.analyze_contact_center_intents(cleaned_text)
            #                 st.markdown("### LLM-Extracted Intents Table")
            #                 if llm_result and 'intent_map' in llm_result:
            #                     st.markdown(llm_result['intent_map'])
            #                     # Save intent map as markdown file
            #                     import datetime
            #                     import hashlib
            #                     import os
            #                     os.makedirs('crawl_results', exist_ok=True)
            #                     safe_url = page_url.replace('https://', '').replace('http://', '').replace('/', '_')
            #                     url_hash = hashlib.md5(page_url.encode('utf-8')).hexdigest()
            #                     filename = f"intent_table_{safe_url}_{url_hash}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            #                     save_path = os.path.join('crawl_results', filename)
            #                     with open(save_path, 'w', encoding='utf-8') as f:
            #                         f.write(llm_result['intent_map'])
            #                     with st.expander("Show LLM Prompt", expanded=False):
            #                         st.code(llm_result.get('llm_prompt', ''), language='markdown')
            #                     st.success(f"Intent table saved to {save_path}")
            #                 else:
            #                     st.warning("No intent map returned by LLM.")
            #             except Exception as e:
            #                 st.error(f"LLM extraction failed: {str(e)}")
            # DO NOT DELETE END
        else:
            st.header("Raw Scraped Data Preview")
            for page_url, page_data in st.session_state.pages.items():
                with st.expander(f"{page_url}"):
                    st.write("**Metadata:**")
                    st.json(page_data.get('metadata', {}))
                    st.write("**Structure:**")
                    st.json(page_data.get('structure', {}))
                    st.write("**Navigation:**")
                    st.json(page_data.get('navigation', {}))
                    import json
                    import hashlib
                    raw_json = json.dumps(page_data, indent=2, ensure_ascii=False)
                    url_hash = hashlib.md5(page_url.encode('utf-8')).hexdigest()
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Save JSON", key=f"save_json_{url_hash}_raw_{page_url}"):
                            import datetime
                            import os
                            safe_url = page_url.replace('https://', '').replace('http://', '').replace('/', '_')
                            filename = f"scraped_{safe_url}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                            save_path = os.path.join('crawl_results', filename)
                            os.makedirs('crawl_results', exist_ok=True)
                            with open(save_path, 'w', encoding='utf-8') as f:
                                f.write(raw_json)
                            st.success(f"Saved to {save_path}")
                    with col2:
                        st.code(raw_json, language='json')
                        st.caption("You can copy the above JSON using the copy button in the code block.")

    # Intent analysis section
    if st.session_state.analyzed_intents:
        st.header("Intent Analysis Results")
        for intent in st.session_state.analyzed_intents:
            display_intent_analysis(intent)
    
    # Contact center intent map section
    if st.session_state.analyzed_intents:
        st.header("Contact Center Intent Map")
        for intent in st.session_state.analyzed_intents:
            if 'intent_map' in intent:
                display_contact_center_intent_map(intent['intent_map'])

    # --- ChromaDB Entries Tab ---
    st.markdown("---")
    tabs = st.tabs(["Intent Maps","Knowledge base"])
    with tabs[0]:
        st.header("ChromaDB Entries")
        from chromadb_store import get_chromadb_client, get_or_create_cleaned_collection
        client = get_chromadb_client()
        collection = get_or_create_cleaned_collection(client)
        # Fetch all entries (ids and metadatas, and documents)
        results = collection.get(include=["metadatas", "documents"])
        ids = results.get("ids", [])
        metadatas = results.get("metadatas", [])
        documents = results.get("documents", [])
        if not ids:
            st.info("No entries found in ChromaDB.")
        else:
            # For intent output
            if 'chromadb_intent_outputs' not in st.session_state:
                st.session_state.chromadb_intent_outputs = {}
            for i, entry_id in enumerate(ids):
                url = metadatas[i].get("source") if metadatas and metadatas[i] else entry_id
                col1, col2 = st.columns([6, 1])
                with col1:
                    st.write(f"**ID:** {entry_id}")
                    st.write(f"**URL:** {url}")
                with col2:
                    if st.button("Generate intents", key=f"gen_intents_{i}"):
                        from llm_processor import LLMProcessor
                        llm_processor = LLMProcessor()
                        doc = documents[i] if documents and i < len(documents) else ""
                        if doc:
                            with st.spinner("Generating intents from ChromaDB entry..."):
                                result = llm_processor.analyze_contact_center_intents(doc)
                                st.session_state.chromadb_intent_outputs[entry_id] = result
                        else:
                            st.warning("No document found for this entry.")
                # Show output if available
                if entry_id in st.session_state.chromadb_intent_outputs:
                    st.markdown("**Intent Map Output:**")
                    output = st.session_state.chromadb_intent_outputs[entry_id]
                    if output and 'intent_map' in output:
                        st.markdown(output['intent_map'])
                    else:
                        st.info("No intent map generated yet.")

if __name__ == "__main__":
    main()
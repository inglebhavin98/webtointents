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
from sitemap_handler import SitemapHandler
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def save_crawled_data(data, urls):
    """Save crawled data to disk."""
    try:
        # Create data directory if it doesn't exist
        os.makedirs('crawled_data', exist_ok=True)
        
        # Create a timestamp for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create a filename based on the first URL
        first_url = next(iter(urls)) if urls else "unknown"
        safe_filename = first_url.replace('https://', '').replace('http://', '').replace('/', '_')
        filename = f"crawl_{timestamp}_{safe_filename}.json"
        
        # Prepare the data for storage
        storage_data = {
            'metadata': {
                'timestamp': timestamp,
                'urls': list(urls),
                'total_urls': len(urls),
                'successful_crawls': len(data)
            },
            'crawled_data': data
        }
        
        # Save to file
        filepath = os.path.join('crawled_data', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(storage_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved crawled data to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error saving crawled data: {str(e)}")
        return None

def load_crawled_data(filepath):
    """Load crawled data from disk."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded crawled data from {filepath}")
        return data
    except Exception as e:
        logger.error(f"Error loading crawled data: {str(e)}")
        return None

def list_crawled_data():
    """List all available crawled data files."""
    try:
        if not os.path.exists('crawled_data'):
            return []
        return [f for f in os.listdir('crawled_data') if f.endswith('.json')]
    except Exception as e:
        logger.error(f"Error listing crawled data: {str(e)}")
        return []

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

def initialize_session_state():
    """Initialize session state variables."""
    try:
        if 'crawled_data' not in st.session_state:
            st.session_state.crawled_data = []
        if 'selected_urls' not in st.session_state:
            st.session_state.selected_urls = set()
        if 'url_hierarchy' not in st.session_state:
            st.session_state.url_hierarchy = None
        if 'total_urls' not in st.session_state:
            st.session_state.total_urls = 0
        if 'selected_count' not in st.session_state:
            st.session_state.selected_count = 0
        if 'checkbox_states' not in st.session_state:
            st.session_state.checkbox_states = {}
        if 'url_to_key_map' not in st.session_state:
            st.session_state.url_to_key_map = {}
        
        # Ensure selected_count matches selected_urls
        st.session_state.selected_count = len(st.session_state.selected_urls)
        
        logger.debug(f"Session state initialized. Selected URLs: {st.session_state.selected_urls}, Count: {st.session_state.selected_count}")
    except Exception as e:
        logger.error(f"Error initializing session state: {str(e)}")
        st.error("Error initializing application state. Please refresh the page.")

def update_selection(key):
    """Callback function to update selected URLs and counter."""
    try:
        is_selected = st.session_state[key]
        url = st.session_state[f'url_for_{key}']
        
        if is_selected:
            st.session_state.selected_urls.add(url)
        else:
            st.session_state.selected_urls.discard(url)
        
        # Update the counter
        st.session_state.selected_count = len(st.session_state.selected_urls)
        logger.debug(f"Updated selection for URL {url}. Selected URLs: {st.session_state.selected_urls}, Count: {st.session_state.selected_count}")
    except Exception as e:
        logger.error(f"Error in update_selection: {str(e)}")
        st.error("Error updating selection. Please try again.")

def update_node_selection(key):
    """Callback function to update all URLs in a node."""
    try:
        is_selected = st.session_state[key]
        urls = st.session_state[f'urls_for_{key}']
        
        if is_selected:
            st.session_state.selected_urls.update(urls)
            # Update all child checkboxes
            for url in urls:
                if url in st.session_state.url_to_key_map:
                    checkbox_key = st.session_state.url_to_key_map[url]
                    st.session_state.checkbox_states[checkbox_key] = True
        else:
            st.session_state.selected_urls.difference_update(urls)
            # Update all child checkboxes
            for url in urls:
                if url in st.session_state.url_to_key_map:
                    checkbox_key = st.session_state.url_to_key_map[url]
                    st.session_state.checkbox_states[checkbox_key] = False
        
        # Update the counter
        st.session_state.selected_count = len(st.session_state.selected_urls)
        logger.debug(f"Updated node selection. Selected URLs: {st.session_state.selected_urls}, Count: {st.session_state.selected_count}")
    except Exception as e:
        logger.error(f"Error in update_node_selection: {str(e)}")
        st.error("Error updating node selection. Please try again.")

def render_url_tree(node, parent_key=''):
    """Render a URL tree node with checkboxes."""
    current_key = f"{parent_key}_{node['id']}" if parent_key else node['id']
    
    # Create columns for checkbox and label
    col1, col2 = st.columns([1, 4])
    
    with col1:
        # Store node URLs in session state
        node_checkbox_key = f"check_{current_key}"
        node_urls = node.get('urls', [])
        st.session_state[f'urls_for_{node_checkbox_key}'] = node_urls
        
        # Calculate if all URLs in this node are selected
        all_selected = all(url in st.session_state.selected_urls for url in node_urls)
        
        # Initialize checkbox state if not exists
        if node_checkbox_key not in st.session_state.checkbox_states:
            st.session_state.checkbox_states[node_checkbox_key] = False
        
        # Checkbox state for the node itself
        checked = st.checkbox(
            ' ',
            key=node_checkbox_key,
            value=all_selected,
            on_change=update_node_selection,
            args=(node_checkbox_key,),
            label_visibility="collapsed"
        )
        st.session_state.checkbox_states[node_checkbox_key] = checked
    
    with col2:
        st.write(node['label'])
        if node_urls:
            with st.expander("View URLs"):
                for url in node_urls:
                    # Create a checkbox for each URL
                    url_checkbox_key = f"url_{current_key}_{url}"
                    st.session_state[f'url_for_{url_checkbox_key}'] = url
                    st.session_state.url_to_key_map[url] = url_checkbox_key
                    
                    # Initialize checkbox state if not exists
                    if url_checkbox_key not in st.session_state.checkbox_states:
                        st.session_state.checkbox_states[url_checkbox_key] = False
                    
                    # Check if this URL is currently selected
                    is_url_selected = url in st.session_state.selected_urls
                    
                    url_checked = st.checkbox(
                        url,
                        key=url_checkbox_key,
                        value=is_url_selected,
                        on_change=update_selection,
                        args=(url_checkbox_key,)
                    )
                    st.session_state.checkbox_states[url_checkbox_key] = url_checked
    
    # Render children
    for child in node.get('children', []):
        render_url_tree(child, current_key)

def main():
    st.title("Web Intent Discovery Tool")
    initialize_session_state()
    
    # Initialize components
    llm_processor, intent_generator = initialize_components()
    if not llm_processor or not intent_generator:
        st.error("Failed to initialize components. Please check the logs.")
        return
    
    crawler = WebsiteCrawler()
    sitemap_handler = SitemapHandler()
    
    # Add a tab for viewing previous crawls
    tab1, tab2 = st.tabs(["Crawl New URLs", "View Previous Crawls"])
    
    with tab1:
        # Input method selection
        input_method = st.radio(
            "Select input method:",
            ["Single URL", "Sitemap"]
        )
        
        if input_method == "Single URL":
            # Original single URL input
            url = st.text_input("Enter URL to crawl:")
            if st.button("Crawl URL"):
                if url:
                    with st.spinner("Crawling URL..."):
                        try:
                            page_data = crawler.crawl_url(url)
                            if page_data:
                                st.session_state.crawled_data = [page_data]
                                # Save the crawled data
                                save_crawled_data([page_data], {url})
                                st.success("Page crawled successfully!")
                        except Exception as e:
                            st.error(f"Error crawling page: {str(e)}")
        
        else:  # Sitemap input
            st.subheader("Sitemap Input")
            sitemap_input = st.text_area(
                "Enter sitemap URL or paste sitemap XML content:",
                height=100
            )
            
            uploaded_file = st.file_uploader("Or upload a sitemap.xml file:", type=['xml'])
            
            if st.button("Process Sitemap"):
                if sitemap_input or uploaded_file:
                    with st.spinner("Processing sitemap..."):
                        try:
                            # Clear previous selections when processing new sitemap
                            st.session_state.selected_urls = set()
                            st.session_state.selected_count = 0
                            st.session_state.checkbox_states = {}
                            st.session_state.url_to_key_map = {}
                            
                            if uploaded_file:
                                urls = parse_uploaded_sitemap(uploaded_file)
                                result = sitemap_handler.process_sitemap('\n'.join(urls))
                            else:
                                result = sitemap_handler.process_sitemap(sitemap_input)
                                
                            st.session_state.url_hierarchy = result['hierarchy']
                            st.session_state.total_urls = result['total_urls']
                            st.success(f"Found {result['total_urls']} URLs in sitemap")
                        except Exception as e:
                            st.error(f"Error processing sitemap: {str(e)}")
                else:
                    st.warning("Please provide either a sitemap URL/content or upload a sitemap file")
            
            # Display URL selection tree if hierarchy exists
            if st.session_state.url_hierarchy:
                st.subheader("Select URLs to crawl")
                
                # URL selection controls
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("Select All"):
                        all_urls = set()
                        for node in st.session_state.url_hierarchy:
                            all_urls.update(node['urls'])
                        st.session_state.selected_urls = all_urls
                        st.session_state.selected_count = len(all_urls)
                        # Update all checkbox states
                        for key in st.session_state.checkbox_states:
                            st.session_state.checkbox_states[key] = True
                        st.rerun()
                
                with col2:
                    st.write(f"Selected URLs: {st.session_state.selected_count} / {st.session_state.total_urls}")
                
                # Render URL tree
                for node in st.session_state.url_hierarchy:
                    render_url_tree(node)
                
                # Crawl selected URLs
                if st.button("Crawl Selected URLs"):
                    if st.session_state.selected_urls:
                        with st.spinner("Crawling selected URLs..."):
                            try:
                                crawled_data = []
                                progress_bar = st.progress(0)
                                total_urls = len(st.session_state.selected_urls)
                                
                                for i, url in enumerate(st.session_state.selected_urls):
                                    try:
                                        logger.info(f"Crawling URL {i+1}/{total_urls}: {url}")
                                        page_data = crawler.crawl_url(url)
                                        if page_data and isinstance(page_data, dict):
                                            # Clean the scraped data before storing
                                            cleaned_data = clean_scraped_data(page_data)
                                            if cleaned_data:
                                                crawled_data.append(cleaned_data)
                                                logger.info(f"Successfully crawled and cleaned data for {url}")
                                            else:
                                                logger.warning(f"No valid data after cleaning for {url}")
                                        else:
                                            logger.warning(f"Invalid or empty data received for {url}")
                                    except Exception as e:
                                        logger.error(f"Error crawling {url}: {str(e)}")
                                        continue
                                    
                                    progress_bar.progress((i + 1) / total_urls)
                                
                                if crawled_data:
                                    st.session_state.crawled_data = crawled_data
                                    # Save the crawled data
                                    save_path = save_crawled_data(crawled_data, st.session_state.selected_urls)
                                    if save_path:
                                        st.success(f"Successfully crawled {len(crawled_data)} out of {total_urls} pages! Data saved to {save_path}")
                                    else:
                                        st.success(f"Successfully crawled {len(crawled_data)} out of {total_urls} pages!")
                                    
                                    # Display summary of crawled data
                                    st.subheader("Crawl Summary")
                                    st.write(f"Total URLs attempted: {total_urls}")
                                    st.write(f"Successfully crawled: {len(crawled_data)}")
                                    st.write(f"Failed: {total_urls - len(crawled_data)}")
                                else:
                                    st.error("No valid data was collected from any of the URLs")
                            except Exception as e:
                                logger.error(f"Error during crawling process: {str(e)}")
                                st.error(f"Error crawling pages: {str(e)}")
                    else:
                        st.warning("Please select at least one URL to crawl")
    
    with tab2:
        st.subheader("Previous Crawls")
        crawled_files = list_crawled_data()
        if crawled_files:
            selected_file = st.selectbox("Select a crawl file:", crawled_files)
            if selected_file:
                filepath = os.path.join('crawled_data', selected_file)
                data = load_crawled_data(filepath)
                if data:
                    st.write("Crawl Metadata:")
                    st.json(data['metadata'])
                    
                    if st.button("Load This Data"):
                        st.session_state.crawled_data = data['crawled_data']
                        st.success("Data loaded successfully!")
                else:
                    st.error("Error loading crawl data")
        else:
            st.info("No previous crawls found")
    
    # Process crawled data
    if st.session_state.crawled_data:
        st.subheader("Process Pages")
        analysis_type = st.radio(
            "Select analysis type:",
            ["Standard Intent Analysis", "Contact Center Intent Map"]
        )
        
        if st.button("Process Pages"):
            with st.spinner("Processing pages..."):
                try:
                    if analysis_type == "Standard Intent Analysis":
                        hierarchy = intent_generator.generate_intent_hierarchy(st.session_state.crawled_data)
                        
                        # Display results
                        st.subheader("Intent Hierarchy")
                        st.json(hierarchy)
                        
                        # Export options
                        export_format = st.selectbox("Export format:", ["JSON", "CSV"])
                        if st.button("Export"):
                            exported_data = intent_generator.export_intents(hierarchy, export_format.lower())
                            st.download_button(
                                "Download",
                                exported_data,
                                file_name=f"intents.{export_format.lower()}",
                                mime="application/json" if export_format == "JSON" else "text/csv"
                            )
                    else:
                        # Contact center intent map
                        successful_analyses = 0
                        st.write("Starting analysis of crawled pages...")
                        
                        for i, page_data in enumerate(st.session_state.crawled_data):
                            try:
                                logger.info(f"Processing page {i+1}/{len(st.session_state.crawled_data)}")
                                
                                # Validate page data
                                if not isinstance(page_data, dict):
                                    logger.error(f"Invalid page data type for page {i+1}: {type(page_data)}")
                                    continue
                                
                                # Log the structure of the page data
                                logger.debug(f"Page data structure for page {i+1}: {list(page_data.keys())}")
                                
                                # Check for required fields
                                required_fields = ['url', 'metadata', 'structure']
                                missing_fields = [field for field in required_fields if field not in page_data]
                                if missing_fields:
                                    logger.error(f"Missing required fields for page {i+1}: {missing_fields}")
                                    continue
                                
                                # Log the content being analyzed
                                logger.debug(f"Analyzing content for URL: {page_data.get('url', 'unknown')}")
                                
                                # Prepare content for analysis
                                content = llm_processor._prepare_content_for_analysis(page_data)
                                if not content:
                                    logger.error(f"Failed to prepare content for analysis for page {i+1}")
                                    continue
                                
                                # Attempt to analyze the page
                                intent_map = llm_processor.analyze_contact_center_intents(content)
                                
                                if intent_map:
                                    logger.info(f"Successfully generated intent map for page {i+1}")
                                    display_contact_center_intent_map(intent_map)
                                    successful_analyses += 1
                                else:
                                    logger.warning(f"No intent map generated for page {i+1}")
                                    st.warning(f"Could not analyze page {i+1}: {page_data.get('url', 'unknown')}")
                            except Exception as e:
                                logger.error(f"Error processing page {i+1}: {str(e)}")
                                st.error(f"Error analyzing page {i+1}: {str(e)}")
                                continue
                        
                        if successful_analyses == 0:
                            st.error("No pages could be successfully analyzed. Please check the logs for details.")
                            # Display debug information
                            st.subheader("Debug Information")
                            st.write("Number of pages attempted:", len(st.session_state.crawled_data))
                            st.write("Sample of first page data structure:", 
                                   {k: type(v) for k, v in st.session_state.crawled_data[0].items()} 
                                   if st.session_state.crawled_data else "No data available")
                        else:
                            st.success(f"Successfully analyzed {successful_analyses} out of {len(st.session_state.crawled_data)} pages")
                except Exception as e:
                    logger.error(f"Error processing pages: {str(e)}")
                    st.error(f"Error processing pages: {str(e)}")

if __name__ == "__main__":
    main()
import streamlit as st
import logging
from crawler import WebsiteCrawler
from llm_processor import LLMProcessor
from intent_generator import IntentGenerator
from src.processors import AnalysisPipeline, PipelineStage, DataCleaner
import json
import os
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
from io import StringIO
from typing import Dict, Any
from collections import defaultdict
from datetime import datetime
import asyncio

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
        pipeline = AnalysisPipeline(llm_processor=llm_processor, progress_callback=update_progress)
        data_cleaner = DataCleaner()
        logger.info("All components initialized successfully")
        return llm_processor, intent_generator, pipeline, data_cleaner
    except Exception as e:
        logger.error(f"Error initializing components: {str(e)}")
        st.error(f"Error initializing components: {str(e)}")
        return None, None, None, None

def update_progress(stage: str, progress: float):
    """Update progress in the Streamlit UI."""
    st.session_state.progress = progress
    st.session_state.current_stage = stage
    st.progress(progress, text=f"Stage: {stage}")

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

def save_crawled_data(data: dict, urls: list):
    """Save crawled data to a local file."""
    try:
        # Create crawled_data directory if it doesn't exist
        os.makedirs('crawled_data', exist_ok=True)
        
        # Generate filename based on timestamp and first URL
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        first_url = urls[0].replace('https://', '').replace('http://', '').replace('/', '_')
        filename = f'crawled_data/crawl_{timestamp}_{first_url}.json'
        
        # Prepare data for storage
        storage_data = {
            'metadata': {
                'timestamp': timestamp,
                'urls': urls,
                'total_urls': len(urls),
                'successful_crawls': len(data)
            },
            'crawled_data': data
        }
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(storage_data, f, indent=2)
        
        logger.info(f"Successfully saved crawled data to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error saving crawled data: {str(e)}")
        return None

def parse_urls(url_input: str) -> list:
    """Parse comma-separated URLs from input string."""
    if not url_input:
        return []
    
    # Split by comma and clean URLs
    urls = [url.strip() for url in url_input.split(',')]
    # Remove empty strings and duplicates
    urls = list(set(filter(None, urls)))
    return urls

async def main():
    st.title("Intent Scraper")
    
    # Initialize components
    crawler = WebsiteCrawler()
    llm_processor, intent_generator, pipeline, data_cleaner = initialize_components()
    if not all([llm_processor, intent_generator, pipeline, data_cleaner]):
        st.error("Failed to initialize required components. Please check the logs for details.")
        return
    
    # Initialize session state
    if 'analyzed_intents' not in st.session_state:
        st.session_state.analyzed_intents = []
    if 'parsed_urls' not in st.session_state:
        st.session_state.parsed_urls = []
    if 'progress' not in st.session_state:
        st.session_state.progress = 0.0
    if 'current_stage' not in st.session_state:
        st.session_state.current_stage = "Not started"
    
    # URL input and sitemap upload interface
    url_input = st.text_input("Enter URLs to analyze (comma-separated)")
    uploaded_file = st.file_uploader("Or upload a sitemap", type=['xml'])
    
    # Parse sitemap if uploaded
    if uploaded_file and st.button("Parse Sitemap"):
        st.session_state.parsed_urls = parse_uploaded_sitemap(uploaded_file)
        if st.session_state.parsed_urls:
            st.success(f"Successfully parsed {len(st.session_state.parsed_urls)} URLs from sitemap")
    
    # Display URL selection if URLs are parsed from sitemap
    if st.session_state.parsed_urls:
        st.subheader("Select URLs to Analyze")
        selected_urls = st.multiselect(
            "Choose URLs to analyze",
            st.session_state.parsed_urls,
            default=st.session_state.parsed_urls[:5]  # Default to first 5 URLs
        )
        st.write(f"Selected {len(selected_urls)} URLs for analysis")
    
    if st.button("Start Analysis"):
        # Get URLs from either comma-separated input or sitemap selection
        urls_to_analyze = []
        if url_input:
            urls_to_analyze = parse_urls(url_input)
        elif 'selected_urls' in locals():
            urls_to_analyze = selected_urls
        
        if urls_to_analyze:
            with st.spinner("Crawling pages..."):
                pages = {}
                progress_bar = st.progress(0)
                
                # Crawl each URL
                for i, url in enumerate(urls_to_analyze):
                    try:
                        logger.info(f"Crawling URL: {url}")
                        with st.spinner(f"Crawling {url}..."):
                            page_data = crawler.crawl_url(url)
                            if page_data:
                                # Clean the scraped data using DataCleaner
                                cleaning_result = data_cleaner.process({'page_data': page_data})
                                if cleaning_result.success:
                                    pages[url] = cleaning_result.data
                                else:
                                    logger.error(f"Error cleaning data for {url}: {cleaning_result.error}")
                                    continue
                        progress_bar.progress((i + 1) / len(urls_to_analyze))
                    except Exception as e:
                        logger.error(f"Error crawling {url}: {str(e)}")
                        continue
                
                if pages:
                    # Save crawled data locally
                    saved_file = save_crawled_data(pages, urls_to_analyze)
                    if saved_file:
                        st.success(f"Successfully saved crawled data to {saved_file}")
                    
                    st.session_state.pages = pages
                    st.session_state.cleaned_pages = None
                    st.session_state.show_cleaned = False
                    st.success(f"Successfully crawled and cleaned {len(pages)} pages")
                    
                    # Process each page through the pipeline
                    st.subheader("Processing Pages")
                    for page_url, page_data in pages.items():
                        with st.expander(f"Processing {page_url}"):
                            try:
                                # Run the pipeline asynchronously
                                pipeline_result = await pipeline.run({
                                    'page_data': page_data,
                                    'analysis_type': 'contact_center'
                                })
                                
                                if pipeline_result.success:
                                    st.success("Analysis completed successfully")
                                    # Store the results
                                    if 'analyzed_intents' not in st.session_state:
                                        st.session_state.analyzed_intents = []
                                    st.session_state.analyzed_intents.append(pipeline_result.data)
                                else:
                                    st.error(f"Analysis failed: {pipeline_result.error}")
                                
                            except Exception as e:
                                logger.error(f"Error processing {page_url}: {str(e)}")
                                st.error(f"Error processing {page_url}: {str(e)}")
                                continue
                    
                    # Display results
                    if st.session_state.analyzed_intents:
                        st.header("Analysis Results")
                        for intent in st.session_state.analyzed_intents:
                            display_intent_analysis(intent)
                else:
                    st.error("No pages could be successfully crawled")
        else:
            st.warning("Please enter URLs or select URLs from the sitemap")

    # Contact center intent map section
    if st.session_state.analyzed_intents:
        st.header("Contact Center Intent Map")
        for intent in st.session_state.analyzed_intents:
            if 'intent_map' in intent:
                display_contact_center_intent_map(intent['intent_map'])

if __name__ == "__main__":
    asyncio.run(main())
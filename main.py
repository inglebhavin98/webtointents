
import streamlit as st
from crawler import WebsiteCrawler
from storage import StorageHandler
import json

def main():
    st.title("Website Scraping & Intent Discovery")
    
    # Initialize crawler and storage
    if 'crawler' not in st.session_state:
        st.session_state.crawler = WebsiteCrawler()
        st.session_state.storage = StorageHandler()
    
    # Input for base URL
    base_url = st.text_input("Enter Base URL", placeholder="https://example.com")
    
    # Start crawl button
    if st.button("Start Crawl and Process"):
        if base_url:
            st.info("Starting crawl process...")
            
            # Create progress bar
            progress_bar = st.progress(0)
            
            try:
                # Parse sitemap
                st.write("📍 Parsing sitemap...")
                urls = st.session_state.crawler.parse_sitemap(base_url)
                
                if not urls:
                    st.warning("No URLs found in sitemap. Crawling base URL...")
                    urls = [base_url]
                
                # Crawl URLs
                results = []
                for i, url in enumerate(urls):
                    st.write(f"🔍 Crawling: {url}")
                    result = st.session_state.crawler.crawl_url(url)
                    if result:
                        results.append(result)
                    progress_bar.progress((i + 1) / len(urls))
                
                # Store results in session state and persistent storage
                st.session_state.crawl_results = results
                st.session_state.show_results = True
                
                # Save to storage
                if results:
                    filename = st.session_state.storage.save_crawl_results(results, base_url)
                    st.success(f"Completed crawling {len(results)} pages! Saved as {filename}")
                    
                    # Show previous crawls
                    st.subheader("Previous Crawls")
                    crawls = st.session_state.storage.list_crawls()
                    for crawl in crawls[:5]:  # Show last 5 crawls
                        st.text(crawl)
                
            except Exception as e:
                st.error(f"Error during crawling: {e}")
        else:
            st.warning("Please enter a base URL")
    
    # Results section
    if st.session_state.get('show_results', False):
        st.subheader("Intent Hierarchy Viewer")
        
        if 'crawl_results' in st.session_state:
            # Show sample of crawled data
            st.json(st.session_state.crawl_results[0] if st.session_state.crawl_results else {})
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "Download Intents JSON",
                    data=json.dumps(st.session_state.crawl_results, indent=2),
                    file_name="intents.json",
                    mime="application/json"
                )
            with col2:
                # Create CSV string
                csv_data = "url,content\n"
                for result in st.session_state.crawl_results:
                    csv_data += f"{result['url']},{result['content'][:100].replace(',', ' ')}\n"
                
                st.download_button(
                    "Download Intents CSV",
                    data=csv_data,
                    file_name="intents.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    main()

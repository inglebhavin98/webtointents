import streamlit as st
from crawler import WebsiteCrawler
from storage import StorageHandler
import json
import os

def main():
    st.title("Intent Mapper")

    # Initialize crawler and storage
    if 'crawler' not in st.session_state:
        st.session_state.crawler = WebsiteCrawler()
        st.session_state.storage = StorageHandler()

    # Input for base URL
    base_url = st.text_input("Enter Base URL", placeholder="https://example.com")

    # First phase: Create sitemap
    if st.button("Create Sitemap"):
        if base_url:
            with st.spinner("Creating sitemap..."):
                sitemap_path, urls = st.session_state.crawler.create_sitemap(base_url)
                st.session_state.urls = urls
                st.success(f"Sitemap created with {len(urls)} URLs!")

                if os.path.exists(sitemap_path):
                    with open(sitemap_path, 'r') as f:
                        st.download_button(
                            "Download Sitemap",
                            f.read(),
                            file_name="sitemap.xml",
                            mime="application/xml"
                        )

    # Second phase: URL Selection and Crawling
    if hasattr(st.session_state, 'urls'):
        st.subheader("Website Structure")
        st.write(f"Found {len(st.session_state.urls)} URLs")

        col1, col2 = st.columns([1, 3])
        with col1:
            select_all = st.checkbox("Select All", value=True)
        
        if 'selected_urls' not in st.session_state:
            st.session_state.selected_urls = st.session_state.urls.copy()
        
        if select_all:
            st.session_state.selected_urls = st.session_state.urls.copy()
        else:
            st.session_state.selected_urls = st.multiselect(
                "Select URLs to crawl",
                st.session_state.urls,
                default=st.session_state.selected_urls
            )

        if st.button("Start Crawl and Process"):
            if base_url:
                st.info("Phase 1: Generating/Loading Sitemap...")
                
                # Create progress bars
                sitemap_progress = st.progress(0)
                crawl_progress = st.progress(0)
                
                results = []
                progress_bar = st.progress(0)
                
                for i, url in enumerate(st.session_state.selected_urls):
                    st.write(f"🔍 Crawling: {url}")
                    result = st.session_state.crawler.crawl_url(url)
                    if result:
                        results.append(result)
                    progress_bar.progress((i + 1) / len(st.session_state.selected_urls))

            if results:
                st.session_state.crawl_results = results
                filename = st.session_state.storage.save_crawl_results(results, base_url)
                st.success(f"Completed crawling {len(results)} pages! Saved as {filename}")

                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "Download Results (JSON)",
                        data=json.dumps(results, indent=2),
                        file_name="results.json",
                        mime="application/json"
                    )
                with col2:
                    csv_data = "url,title,description\n"
                    for result in results:
                        csv_data += f"{result['url']},{result['metadata']['title']},{result['metadata']['description']}\n"
                    st.download_button(
                        "Download Results (CSV)",
                        data=csv_data,
                        file_name="results.csv",
                        mime="text/csv"
                    )

if __name__ == "__main__":
    main()
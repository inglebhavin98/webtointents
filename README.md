# Intent Discovery Tool

A powerful web application for scraping websites, extracting structured content, performing LLM-based analysis, and generating intent structures to support contact center transformation use cases.

## Overview

The Intent Discovery Tool is designed to help contact center transformation teams analyze website content and generate structured intent maps. It uses advanced LLM (Large Language Model) processing to understand user intents, goals, and potential interactions from website content.

## Features

- **Website Crawling**: Automated crawling of websites with support for sitemap parsing
- **Content Extraction**: Intelligent extraction of structured content including headers, FAQs, and product information
- **LLM Analysis**: Advanced content analysis using LLM for intent discovery and mapping
- **Intent Hierarchy**: Generation of hierarchical intent structures with confidence scores
- **Contact Center Focus**: Specialized analysis for contact center transformation use cases
- **Data Storage**: Persistent storage using ChromaDB for efficient retrieval and similarity search
- **Web Interface**: Streamlit-based dashboard for easy interaction and visualization

## Project Structure

```
.
├── main.py                 # Main application entry point
├── crawler.py             # Website crawling functionality
├── llm_processor.py       # LLM processing and analysis
├── intent_generator.py    # Intent generation and hierarchy creation
├── dashboard.py           # Streamlit dashboard interface
├── chromadb_store.py      # ChromaDB storage management
├── storage.py             # File-based storage handler
├── intents_chromadb_tab.py # ChromaDB visualization component
├── test_llm.py           # LLM functionality tests
├── test_chromadb.py      # ChromaDB functionality tests
├── check_chromadb.py     # ChromaDB inspection utility
├── contact_center_intent_prompt.txt # Specialized prompt template
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Project configuration
├── .replit              # Replit deployment configuration
├── TODO.md              # Planned improvements and enhancements
├── .python-version      # Python version specification
├── uv.lock             # Dependency lock file
├── generated-icon.png  # Application icon
├── sitemap.xml        # Default sitemap file
├── .gitignore        # Git ignore rules
├── src/              # Source code directory
├── config/           # Configuration files
├── sitemaps/         # Generated sitemap files
├── crawl_results/    # Stored crawl results
├── chroma_db_store/  # ChromaDB persistent storage
├── build/           # Build artifacts
├── python_template.egg-info/ # Package metadata
└── attached_assets/ # Additional resources and specifications
```

## Core Components

### 1. Website Crawler (`crawler.py`)
- Sitemap parsing and generation
- Hierarchical website crawling
- Content extraction with metadata
- Support for dynamic content using Selenium

### 2. LLM Processor (`llm_processor.py`)
- Content analysis and context extraction
- Intent detection and classification
- Question generation and paraphrasing
- Response generation for contact center use cases

### 3. Intent Generator (`intent_generator.py`)
- Intent hierarchy creation
- Collision detection
- URL-based organization
- Export functionality (JSON/CSV)

### 4. Storage System
- ChromaDB for vector storage (`chromadb_store.py`)
- File-based storage for crawl results (`storage.py`)
- Efficient similarity search and retrieval

### 5. Dashboard (`dashboard.py`)
- Streamlit-based web interface
- Real-time processing status
- Intent visualization
- Export capabilities

## Setup and Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```
   GROQ_API_KEY=your_api_key
   SITE_URL=http://localhost:8501
   SITE_NAME=Intent Discovery Tool
   ```

4. Run the application:
   ```bash
   streamlit run main.py
   ```

## Usage

1. **Start Crawling**:
   - Enter the base URL of the website to analyze
   - The tool will automatically crawl and process the content

2. **View Results**:
   - Access the dashboard to see the generated intent hierarchy
   - Explore individual intents and their relationships
   - View confidence scores and source context

3. **Export Data**:
   - Download intent structures in JSON or CSV format
   - Access raw crawl results from the storage system

## Development

### Testing
- Run LLM tests: `python test_llm.py`
- Check ChromaDB: `python check_chromadb.py`
- Test ChromaDB functionality: `python test_chromadb.py`

### Project Structure
- `src/`: Source code directory (currently empty, for future organization)
- `config/`: Configuration files
- `sitemaps/`: Generated sitemap files
- `crawl_results/`: Stored crawl results
- `chroma_db_store/`: ChromaDB persistent storage

## Planned Improvements

See `TODO.md` for detailed planned improvements, including:
- Enhanced context extraction
- Comprehensive content analysis
- Learning capabilities
- Infrastructure improvements
- UI/UX enhancements
- Error handling and logging
- Performance optimization
- Testing and validation
- Documentation updates

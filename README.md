# Intent Discovery Tool

A Streamlit-based web application built as a **learning MVP** to understand how LLMs work for two core problems: (1) **intent extraction from unstructured web content**, and (2) **retrieval-augmented generation (RAG)** for conversational Q&A.

The project demonstrates a full pipeline from web scraping to vector storage to LLM-powered output — serving as both an intent discovery engine and a working chatbot backend.

## Purpose

This project was created to learn the mechanics of modern LLM applications hands-on, not as a production tool for contact center teams. It explores:

- How LLMs extract structured intent tables from raw website text
- How RAG pipelines combine vector search with LLM synthesis
- How to wire crawling, cleaning, embedding, storage, and inference into a single Streamlit app
- How different prompts and model choices affect output quality

## What It Does

This is **one app with two parallel products**, both built on the same shared pipeline:

| Mode | Input | Output | Who Uses It |
|------|-------|--------|-------------|
| **Intent Discovery** | Website URLs or XML sitemap | Structured intent tables (markdown) | Analysts mapping customer needs from web content |
| **RAG Chat** | Natural language questions | Synthesized answers with source citations | End-users querying the scraped knowledge base |

Both modes share the same crawling, cleaning, embedding, and vector storage pipeline. The only difference is the final LLM prompt and how the output is presented.

### End-to-End Flow

1. **Input** — User provides URLs or uploads an XML sitemap.
2. **Crawl** — A headless browser (Selenium/Chrome) visits each page and scrapes metadata, headers, paragraphs, FAQs, forms, and links.
3. **Clean & Chunk** — Raw page data is deduplicated, chunked by headers, normalized (CTAs removed, acronyms expanded), and stored.
4. **Embed & Store** — Cleaned text is embedded using a local SentenceTransformer model (`all-MiniLM-L6-v2`) and stored in **ChromaDB** for similarity search.
5. **LLM Analysis** — Cleaned text is sent to an LLM (currently **Groq** via `llama-3.3-70b-versatile`) using a specialized prompt to extract a markdown-formatted intent table: Intent Name, User Goal, Sample Phrases, and Source Context.
6. **Knowledge Base Q&A** — Users can chat against scraped pages via a retrieval-augmented Q&A tab that queries ChromaDB and synthesizes answers with the LLM.
7. **Dashboard / Batch Review** — A separate "Dashboard" view lists all stored pages, allows batch intent extraction, and clusters/summarizes intents into frequency tables.

---

## Architecture

The project is a modular, script-based pipeline driven by a **Streamlit** frontend. There is no formal backend API or task queue — all orchestration happens inside the Streamlit app.

### Component Map

| Component | Role | Key File |
|-----------|------|----------|
| **Frontend / Router** | Streamlit app, page routing, UI layout | `main.py` |
| **Crawler** | Headless browser scraping + sitemap parsing | `crawler.py` |
| **LLM Engine** | Prompt construction, API calls, JSON parsing | `llm_processor.py` |
| **Intent Logic** | URL hierarchies, collision detection, batching | `intent_generator.py` |
| **Vector Store** | ChromaDB client, embedding, similarity search | `chromadb_store.py` |
| **File Store** | JSON serialization of crawl results | `storage.py` |
| **Dashboard** | Batch processing UI, async LLM calls, clustering | `dashboard.py` |
| **Intents Tab** | Read-only viewer for the `intents` ChromaDB collection | `intents_chromadb_tab.py` |

### Data Flow

```
User (Streamlit)
   |
   v
main.py ------> crawler.py (Selenium + BeautifulSoup)
   |                |
   |                v
   |         storage.py (JSON files in crawl_results/)
   |                |
   |                v
   |         chromadb_store.py (embed + upsert to ChromaDB)
   |                |
   v                v
llm_processor.py <--- (reads cleaned text from ChromaDB or session state)
   |
   v
intent_generator.py (URL hierarchy, collision logic)
   |
   v
dashboard.py / main.py (render results as markdown tables)
```

### How RAG Chat Works

The chat feature uses the same `cleaned_pages` ChromaDB collection that intent discovery uses:

1. **User asks a question** in the "Knowledge Base Chat" tab.
2. **Query embedding** — The question is embedded locally using `all-MiniLM-L6-v2`.
3. **Retrieval** — ChromaDB returns the top-3 most similar page chunks + metadata (source URLs).
4. **Prompt composition** — Retrieved chunks + the original question are composed into a single prompt.
5. **LLM synthesis** — Groq returns an answer with inline source references.
6. **Display** — Answer is shown in a simple chat history UI.

This demonstrates a minimal but complete RAG pipeline with no external vector DB hosting.

### Key Design Decisions

- **LLM-Only over Hybrid NLP** — The project moved away from spaCy/BERTopic to a pure LLM approach. `intent_generator.py` still contains unused NLP-era batching logic.
- **Local Embeddings + Cloud LLM** — Embedding is done locally for free; heavy inference is offloaded to Groq.
- **Dual Persistence** — Every scraped page is saved both as a local JSON artifact and as a ChromaDB vector entry. This makes the pipeline debuggable.
- **Prompt-Driven Schema** — The LLM is expected to return strict JSON or markdown tables. Prompt templates are stored in external files (`contact_center_intent_prompt.txt`) for easier tuning.
- **Session-State-Driven UI** — Streamlit's `st.session_state` is used heavily to pass data between steps.
- **URLs as ChromaDB IDs** — Simple deduplication by upsert, but no versioning.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI | Streamlit (`1.45.1`) |
| Web Scraping | Selenium (`4.32.0`) with `webdriver-manager`, BeautifulSoup (`4.13.4`), `requests` |
| LLM API | Groq SDK, model `llama-3.3-70b-versatile` |
| Embeddings | Local `sentence-transformers` (`all-MiniLM-L6-v2`, 384-dim) |
| Vector DB | ChromaDB (`0.4.24`) with persistent storage in `./chroma_db_store` |
| Env Management | `python-dotenv` |

> **Note:** `scrapy` is listed in `requirements.txt` but unused in the current codebase.

---

## Project Structure

```
.
├── main.py                 # Main Streamlit application entry point
├── crawler.py              # Website crawling (Selenium + BeautifulSoup)
├── llm_processor.py        # LLM processing and analysis
├── intent_generator.py     # Intent generation and hierarchy creation
├── dashboard.py            # Streamlit dashboard for batch processing
├── chromadb_store.py       # ChromaDB storage management
├── storage.py              # File-based JSON storage handler
├── intents_chromadb_tab.py # ChromaDB intents viewer component
├── contact_center_intent_prompt.txt  # Specialized LLM prompt template
├── requirements.txt        # Python dependencies
├── pyproject.toml           # Project configuration
├── .replit                  # Replit deployment configuration
├── .python-version          # Python version specification
├── uv.lock                  # Dependency lock file
├── TODO.md                  # Planned improvements and enhancements
├── README.md                # This file
├── sitemap.xml              # Default sitemap file
├── .gitignore               # Git ignore rules
├── generated-icon.png       # Application icon
├── attached_assets/         # Additional resources
├── sitemaps/                # Generated sitemap files
├── crawl_results/           # Stored crawl results (JSON)
└── chroma_db_store/         # ChromaDB persistent storage
```

---

## Core Components

### 1. Website Crawler (`crawler.py`)
- Sitemap parsing and generation
- Hierarchical website crawling via headless Chrome
- Content extraction: metadata, headers (`h1/h2/h3`), paragraphs, FAQs, forms, links
- Heuristic page-type classification (`faq`, `form`, `product`, `contact`, `about`)
- Support for dynamic content using Selenium

### 2. LLM Processor (`llm_processor.py`)
- `extract_page_context(text)` — Step 1: classify page type, user context, topic analysis, intent signals (strict JSON)
- `analyze_content(text)` — Step 2: richer JSON with primary intent, user goals, Q&A pairs, entities, topic hierarchy, suggested bot responses
- `process_page_for_intents(page_data)` — Orchestrates the two-step pipeline
- `analyze_contact_center_intents(html_content)` — **Active specialized method.** Loads `contact_center_intent_prompt.txt`, injects cleaned page text, returns a markdown intent table

### 3. Intent Generator (`intent_generator.py`)
- `create_url_hierarchy(urls)` — Groups URLs by first path segment
- `detect_intent_collisions(intents)` — Compares intents in batches of 5 using the LLM to find semantic duplicates or overlaps
- `generate_intent_hierarchy(crawled_data)` — Drives the full batch pipeline: URL hierarchy, per-page LLM processing, collision detection, hierarchy synthesis
- `export_intents(hierarchy, format='json')` — Serializes to JSON or CSV

### 4. Storage System
- **ChromaDB** (`chromadb_store.py`) — Two collections: `cleaned_pages` (raw embedded text) and `intents` (LLM analysis results). URLs are used as document IDs.
- **File-based** (`storage.py`) — JSON serialization of crawl results into `crawl_results/`.

### 5. Dashboard (`dashboard.py`)
- Streamlit-based web interface for batch processing
- Shows total pages in ChromaDB
- "Process for Intents" button: triggers async LLM calls for up to 5 pages with rate-limit sleep
- `cluster_and_summarize_intents_llm()` — Reads all intent documents and asks the LLM to cluster them into a markdown frequency table

---

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

---

## Usage

1. **Start Crawling**:
   - Enter the base URL of the website to analyze, or upload an XML sitemap.
   - The tool will automatically crawl and process the content.

2. **View Results**:
   - Access the dashboard to see the generated intent hierarchy.
   - Explore individual intents and their relationships.
   - View confidence scores and source context.

3. **Export Data**:
   - Download intent structures in JSON or CSV format.
   - Access raw crawl results from the storage system.

---

## Testing

- Run LLM tests: `python test_llm.py`
- Check ChromaDB: `python check_chromadb.py`
- Test ChromaDB functionality: `python test_chromadb.py`

---

## Known Limitations & Rough Edges

The project is a **functional prototype / MVP** built to learn LLM mechanics. It demonstrates the core pipeline successfully but carries significant technical debt from rapid iteration.

### Code Quality & Dead Code
- **`main.py` contains large commented-out UI sections** marked "DO NOT DELETE" for raw data preview, manual cleaning buttons, and inline LLM extraction loops.
- **Duplicate method definitions in `llm_processor.py`** — `analyze_contact_center_intents` is defined twice (first expecting `Dict[str, Any]`, second expecting `str`). The second overrides the first at runtime.
- **Broken collision detection** — `IntentGenerator.detect_intent_collisions` calls `self.llm_processor.analyze_intent_similarity(intent_data)`, but this method **does not exist** in `LLMProcessor`.
- **Unused imports** — Several imports in `main.py` are only used in commented-out sections.

### API and Model Drift
- **Mixed API styles** — Some methods still call the legacy `openai.ChatCompletion.create` (with OpenRouter headers) while others call `self.client.chat.completions.create` (Groq). The `openai` calls may fail without correct base URL configuration.
- **Rate-limit sleep in async path** — `dashboard.py`'s `async_generate_intent` hardcodes `await asyncio.sleep(6)`. This is fragile and non-configurable.
- **No retry logic** — `llm_processor.py` does not implement retries for API failures, timeouts, or malformed JSON responses.

### Data Model & Storage Issues
- **ChromaDB ID collision** — URLs are used as ChromaDB IDs. Recrawling a URL overwrites the old entry with no versioning.
- **Flat intent storage** — The `intents` collection stores a JSON-serialized list of intents per document, but the schema is loose.
- **No deduplication across pages** — Dashboard batch processing limits to 5 pages arbitrarily and does not deduplicate intents before clustering.

### UI / UX Limitations
- **Synchronous blocking** — The "Start Analysis" loop in `main.py` is synchronous; crawling 20+ pages would freeze the UI.
- **No progress granularity** — Progress bar for crawling, but none for the LLM analysis phase.
- **Minimal error surfacing** — When `json.loads` fails, the UI shows a generic warning, hiding the actual parse error.
- **Raw text exposure** — The knowledge base chat dumps top-3 chunks directly into the LLM context with no max-length truncation, so long pages could exceed token limits.

### Architecture & Testing
- **No unit tests in practice** — Core logic (`main.py`, `dashboard.py`) is tightly coupled to Streamlit's global state, making it untestable without mocking the entire framework.
- **No configuration file** — All behavior (model names, collection names, rate-limit sleeps, max crawl pages) is hardcoded. The `.env` file is only used for API keys.

---

## Planned Improvements

See `TODO.md` for detailed planned improvements, including:
- Enhanced context extraction
- Comprehensive content analysis
- Learning capabilities
- Infrastructure improvements (remove old NLP dependencies)
- UI/UX enhancements
- Error handling and logging
- Performance optimization
- Testing and validation
- Documentation updates

Priority order:
1. Infrastructure Improvements (remove old dependencies)
2. Enhanced Context Extraction
3. Comprehensive Content Analysis
4. Error Handling & Logging
5. UI/UX Improvements
6. Learning Capabilities
7. Performance Optimization
8. Testing & Validation
9. Documentation

---

## Future Directions: Understanding LLMs

This project is a sandbox for learning. The most valuable next steps are experiments that deepen understanding of how different LLM configurations affect quality, latency, and cost.

| Direction | What You'd Learn |
|-----------|-----------------|
| **Swap Groq for local LLM (Ollama + llama3)** | How inference works locally, latency/quality tradeoffs |
| **Add a "compare models" feature** | See how different LLMs (GPT-4, Claude, local) extract intents differently from the same page |
| **Build a simple evaluation framework** | Ground truth scoring: "did the LLM miss any obvious intents?" |
| **Try different embedding models** | `all-MiniLM` vs `BGE` vs OpenAI embeddings — how does retrieval quality change? |
| **Add multi-turn conversation memory** | Current chat is single-turn; add conversation history to the RAG context |
| **Experiment with prompt chaining** | Break the intent extraction into 3-4 smaller LLM calls instead of one big prompt |

These experiments map directly to production LLM system design decisions: model selection, prompt engineering, evaluation methodology, and RAG architecture. The knowledge gained here transfers to any serious LLM application.

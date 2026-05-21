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

The project is a modular, script-based pipeline driven by a **Streamlit** frontend. There is no formal backend API or task queue — all orchestration happens inside the Streamlit app (`main.py`), which acts as both the UI layer and the workflow engine.

### Component Map

| Component | Role | Key File | Key Classes / Functions |
|-----------|------|----------|------------------------|
| **Frontend / Router** | Streamlit app, page routing, tab layout, session state management | `main.py` | `main()`, `initialize_components()`, `clean_scraped_data()`, `parse_uploaded_sitemap()`, `display_contact_center_intent_map()` |
| **Crawler** | Headless browser scraping + sitemap parsing/generation | `crawler.py` | `WebsiteCrawler`, `crawl_url()`, `crawl()`, `create_sitemap()`, `parse_sitemap()` |
| **LLM Engine** | Prompt construction, Groq API calls, JSON/markdown parsing, fallback handling | `llm_processor.py` | `LLMProcessor`, `extract_page_context()`, `analyze_content()`, `process_page_for_intents()`, `analyze_contact_center_intents()`, `generate_intent()` |
| **Intent Logic** | URL hierarchies, collision detection (broken), batch orchestration, export | `intent_generator.py` | `IntentGenerator`, `create_url_hierarchy()`, `detect_intent_collisions()`, `generate_intent_hierarchy()`, `export_intents()` |
| **Vector Store** | ChromaDB client, local embedding, similarity search, collection management | `chromadb_store.py` | `get_chromadb_client()`, `get_or_create_cleaned_collection()`, `get_or_create_intents_collection()`, `embed_text()`, `upsert_cleaned_page()`, `query_similar_pages()` |
| **File Store** | JSON serialization of crawl results | `storage.py` | `StorageHandler`, `save_crawl_results()`, `get_crawl_results()` |
| **Dashboard** | Batch processing UI, async LLM calls, clustering/summarization | `dashboard.py` | `dashboard_route()`, `call_llm_for_intents()`, `async_generate_intent()`, `cluster_and_summarize_intents_llm()` |
| **Intents Tab** | Read-only viewer for the `intents` ChromaDB collection | `intents_chromadb_tab.py` | `show_intents_chromadb_tab()` |

---

### Data Flow

The system has a single ingestion pipeline that fans out into two consumption paths.

#### Ingestion Pipeline (Shared by Both Modes)

```
User input (URLs or sitemap XML)
   |
   v
main.py: parse_uploaded_sitemap()  OR  url_input.split(',')
   |
   v
crawler.py: WebsiteCrawler.crawl_url(url)
   |   - Spins up headless Chrome via webdriver-manager
   |   - Waits for <body> with WebDriverWait
   |   - Extracts: title, meta, canonical, h1/h2/h3, paragraphs, FAQs, forms, links
   |   - Classifies page type heuristically (faq/form/product/contact/about)
   |   - Returns nested dict:
   |       {"url": "...",
   |        "metadata": {"title": "...", "description": "...", "page_type": "..."},
   |        "structure": {"headers": {"h1": [...], "h2": [...]},
   |                      "main_content": [{"tag": "p", "text": "..."}, ...],
   |                      "faqs": [...], "forms": [...]},
   |        "navigation": {"internal_links": [...], "external_links": [...]}}
   |
   v
main.py: clean_scraped_data(page_data)
   |   - Deduplicates headers, FAQs, content blocks (case-insensitive, order-preserving)
   |   - Recursively removes empty/null/[]/{} fields
   |   - Chunks content by h2/h3 boundaries into `page_data['chunks']`
   |   - Removes CTA patterns: "click here", "contact us", "learn more", "sign up", "get started"
   |   - Expands acronyms: FAQ → "Frequently Asked Questions"
   |   - Tags each chunk with `chunk_id`
   |   - Returns cleaned dict
   |
   +------------------>  File persistence (JSON)
   |       main.py writes: crawl_results/cleaned_<safe_url>_<hash>_<timestamp>.json
   |
   +------------------>  Vector persistence (ChromaDB)
           chromadb_store.py: upsert_cleaned_page(url, cleaned)
               - Flattens cleaned dict into a single text string
                 (prioritizes keys: chunks → content → headers → faqs_clean)
               - Falls back to recursive string extraction if empty
               - Embeds via SentenceTransformer('all-MiniLM-L6-v2') → 384-dim float vector
               - Upserts into collection `cleaned_pages` with URL as the document ID
                 {ids: [url], embeddings: [vec], documents: [text], metadatas: [{"source": url}]}
```

#### Consumption Path A: Intent Discovery

There are **two sub-paths** for intent extraction, depending on where the user clicks:

**Path A1 — Per-Page Intent Extraction ("Intent Maps" tab in `main.py`)**

```
main.py Intent Maps tab
   |
   v
User clicks "Generate intents" next to a ChromaDB entry
   |
   v
llm_processor.py: LLMProcessor.analyze_contact_center_intents(doc_text)
   |   - Reads contact_center_intent_prompt.txt from disk at __init__ time
   |   - Injects the cleaned page text into the template via .format()
   |   - Calls Groq client.chat.completions.create()
   |       model="llama-3.3-70b-versatile", temperature=0.3
   |   - Returns: {"intent_map": "<markdown table>", "llm_prompt": "<full prompt text>"}
   |
   v
main.py renders markdown table with st.markdown()
   |
   v
Optionally saves as .md file to crawl_results/intent_table_...
```

**Path A2 — Batch Intent Extraction ("Dashboard" page in `dashboard.py`)**

```
dashboard.py: dashboard_route()
   |
   v
User clicks "Process for Intents"
   |
   v
Reads all documents from `cleaned_pages` collection (max 5 hardcoded)
   |
   v
For each document:
   dashboard.py: async_generate_intent()
       - Wraps call_llm_for_intents() in asyncio.run_in_executor(None, ...)
       - Uses INTENT_EXTRACTION_PROMPT (defined inline in dashboard.py):
         "identify the top 10 most probable user intents... output a plain numbered list"
       - Calls llm.generate_intent(prompt) → gets raw text
       - Parses numbered list into Python list via regex: `l.split('.', 1)[1].strip()`
       - Sleeps 6 seconds between calls to avoid Groq rate limits
   |
   v
Stores results in `intents` collection:
   {documents: [json.dumps(intent_list)], metadatas: [{"url": url}], ids: [doc_id]}
   |
   v
dashboard.py: cluster_and_summarize_intents_llm(intents_collection)
   - Reads all intent documents back from ChromaDB
   - Flattens and deduplicates (best-effort)
   - Sends to LLM with clustering prompt: "Cluster these intents into groups of similar meaning..."
   - Renders markdown frequency table
```

#### Consumption Path B: RAG Chat ("Knowledge Base" tab in `main.py`)

```
main.py Knowledge Base Chat tab
   |
   v
User types a question and clicks "Send"
   |
   v
chromadb_store.py: embed_text(user_query)
   - SentenceTransformer encodes query → 384-dim vector
   |
   v
ChromaDB `cleaned_pages` collection.query()
   - query_embeddings=[query_vec], n_results=3
   - Returns top-3 document chunks + metadata (source URLs)
   |
   v
main.py composes RAG prompt inline:
   "You are a helpful assistant. Use the following context from the knowledge base..."
   + "\n---\n".join(top_chunks)
   + "\n\nUser question: {user_query}\n\nAnswer:"
   |
   v
Groq chat.completions.create()
   - model="llama-3.3-70b-versatile", temperature=0.5
   - system: "You are a helpful assistant for knowledge base Q&A."
   |
   v
Answer appended to st.session_state.kb_chat_history
   - List of {"role": "user"/"assistant", "content": "..."} dicts
   - Rendered as simple markdown in a loop
```

---

### ChromaDB Schema

Two collections are used. Both use the URL (or a doc ID derived from it) as the ChromaDB document ID.

| Collection | Purpose | Document Content | Metadata | Embedding Model |
|------------|---------|-------------------|----------|-----------------|
| `cleaned_pages` | Raw scraped and cleaned page text for RAG and intent input | Flattened text string from all chunks/content/headers/faqs | `{"source": "https://..."}` | `all-MiniLM-L6-v2` (384-dim) |
| `intents` | LLM-generated intent lists from batch dashboard processing | `json.dumps(["intent1", "intent2", ...])` | `{"url": "https://..."}` | None (no embedding stored for intent docs) |

**Important:** URLs are used as ChromaDB IDs. Re-crawling the same URL performs an **upsert**, which silently overwrites the previous entry. There is no versioning or timestamp in the metadata.

---

### Session State Management

Streamlit's `st.session_state` is the application's only runtime state store. Key session state keys and their purposes:

| Key | Set In | Purpose |
|-----|--------|---------|
| `sitemap_urls` | `parse_uploaded_sitemap()` | Stores parsed URLs from uploaded sitemap XML |
| `pages` | `main.py` "Start Analysis" | Raw scraped page dicts keyed by URL |
| `cleaned_pages` | `main.py` "Start Analysis" | Cleaned page dicts keyed by URL |
| `show_cleaned` | `main.py` "Start Analysis" | Boolean toggle for previewing cleaned vs raw data |
| `analyzed_intents` | `main.py` | List of fully analyzed intent dicts (legacy two-step format) |
| `chromadb_intent_outputs` | `main.py` Intent Maps tab | Dict mapping ChromaDB entry ID → `{"intent_map": "...", "llm_prompt": "..."}` |
| `kb_chat_history` | `main.py` Knowledge Base tab | List of `{"role": "user"/"assistant", "content": "..."}` chat messages |
| `intents_chromadb_outputs` | `intents_chromadb_tab.py` | Dict mapping intent ID → raw document string for expander display |
| `stop_crawl` | `stop_crawl_callback()` | Boolean flag checked once per loop iteration to break the crawling loop |

---

### Prompt Engineering Architecture

The project uses **external prompt files** for the main intent extraction template and **inline prompts** for everything else.

| Prompt | Location | Input | Output Format | Model |
|--------|----------|-------|---------------|-------|
| Contact Center Intent Map | `contact_center_intent_prompt.txt` | Flattened page text | Markdown table: \| Intent Name \| User Goal \| Sample Phrases \| Source Context \| | `llama-3.3-70b-versatile` |
| Batch Intent List | Inline in `dashboard.py` (`INTENT_EXTRACTION_PROMPT`) | Flattened page text | Plain numbered list of 10 intents | `llama-3.3-70b-versatile` |
| RAG Synthesis | Inline in `main.py` | Top-3 ChromaDB chunks + user question | Free-form answer text | `llama-3.3-70b-versatile` |
| Context Extraction (legacy) | Inline in `llm_processor.py` | Raw page text | Strict JSON with page_type, user_context, topic_analysis, intent_signals | `llama-3.3-70b-versatile` |
| Content Analysis (legacy) | Inline in `llm_processor.py` | Context JSON + raw text | Strict JSON with primary_intent, user_goals, Q&A pairs, entities, topic_hierarchy | `llama-3.3-70b-versatile` |
| Intent Clustering | Inline in `dashboard.py` | Flattened list of all intents | Markdown frequency table | `llama-3.3-70b-versatile` |

**Prompt chaining:** The legacy two-step pipeline (`extract_page_context` → `analyze_content`) chains LLM calls: Step 1 produces a JSON context object that is serialized and fed into Step 2's prompt as context. This is currently unused in the active flow (the contact center prompt is a single-shot call).

**JSON schema enforcement:** All legacy prompts include explicit JSON schemas in the prompt text and set `temperature=0.3` to reduce hallucination. The active contact center prompt uses a markdown table schema instead.

---

### Error Handling Patterns

The codebase uses a consistent but basic error handling strategy:

1. **Defensive JSON parsing** — Every `json.loads()` is wrapped in `try/except json.JSONDecodeError`. On failure, the method returns `None` and logs an error. Callers check `if result:` before using it.
2. **Silent failure on storage** — ChromaDB upsert failures in `main.py` are caught and shown as `st.warning()` but do not stop the pipeline. JSON save failures are unhandled (will raise).
3. **No retry logic** — API calls in `llm_processor.py` have no retry, backoff, or timeout handling. A single Groq failure returns `None` and bubbles up as a generic Streamlit error.
4. **Graceful degradation on missing methods** — `IntentGenerator.detect_intent_collisions` calls `self.llm_processor.analyze_intent_similarity()`, which does not exist. This would raise `AttributeError` if that code path were ever executed, but the dashboard batch flow bypasses collision detection entirely.
5. **Session state guards** — Keys are initialized with `if 'key' not in st.session_state` blocks before use to avoid `KeyError`.

---

### Rate Limiting & Async

The only async code in the project is in `dashboard.py`:

- `async_generate_intent()` uses `asyncio.run_in_executor(None, call_llm_for_intents, ...)` to run the blocking Groq call in a thread pool.
- After each call, it `await asyncio.sleep(6)` to respect Groq rate limits.
- The outer `dashboard_route()` creates a new event loop with `asyncio.new_event_loop()`, queues up to 5 tasks, and runs them with `asyncio.as_completed()`.
- There is no actual parallelism — the sleep serializes execution. It is a cooperative throttle, not true concurrent batching.

---

### Key Design Decisions

- **LLM-Only over Hybrid NLP** — The project moved away from spaCy/BERTopic to a pure LLM approach. `intent_generator.py` still contains unused NLP-era batching logic.
- **Local Embeddings + Cloud LLM** — Embedding is done locally for free; heavy inference is offloaded to Groq.
- **Dual Persistence** — Every scraped page is saved both as a local JSON artifact and as a ChromaDB vector entry. This makes the pipeline debuggable.
- **Prompt-Driven Schema** — The LLM is expected to return strict JSON or markdown tables. Prompt templates are stored in external files (`contact_center_intent_prompt.txt`) for easier tuning.
- **Session-State-Driven UI** — Streamlit's `st.session_state` is used heavily to pass data between steps. There is no backend API or database session layer.
- **URLs as ChromaDB IDs** — Simple deduplication by upsert, but no versioning.
- **No configuration abstraction** — All behavior (model names, collection names, rate-limit sleeps, max crawl pages) is hardcoded in source files. The `.env` file is only used for `GROQ_API_KEY`.

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

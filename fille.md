# Part 1 — Beginner to Intermediate: How the Smart Filter Selector Works

This is the **first part** of your deep learning guide.

## 1) What this project does

The system reads a natural-language query (English/French/Spanish), understands its meaning, and returns the most relevant filters from a predefined catalog.

Example:
- Query: "We are designing an ERTMS signaling system for high-speed trains"
- Output filters: Railway, Signalling, ERTMS, High Speed Lines

So this is an **AI-assisted filter recommendation service**.

## 2) High-level architecture

Runtime code is in:
- `/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector`

Main layers:
1. **API layer** (`app/routes/filter_routes.py`) receives HTTP requests.
2. **Orchestrator** (`app/services/hybrid_selector.py`) runs the pipeline.
3. **Retrieval layer** (`app/services/embedding_service.py`) finds semantically similar filter items.
4. **Reasoning layer** (`app/services/llm_service.py`) refines candidates using an LLM.
5. **Level inference** (`app/services/level_detector.py`) predicts user levels.
6. **Translation** (`app/services/translation_service.py`) normalizes multilingual input.
7. **Data layer** (`data/*.json`, `data/chroma_db`) stores taxonomy and embeddings.

## 3) End-to-end request workflow

When `/api/filter/analyze-query` is called:

1. Request JSON is validated with `FilterQueryRequest`.
2. Query language is detected and translated to English if needed.
3. Query embedding is generated with Ollama.
4. Similarity search compares query embedding with all precomputed filter embeddings.
5. Top candidates go to LLM refinement.
6. LLM returns structured JSON (`reducedFilters`, `confidence`, `reasoning`).
7. Level detector runs a second LLM pass for seniority/tool/language levels.
8. Final response combines all stages + timing.

## 4) Core AI concepts used here

### Embeddings
Embeddings are vectors representing semantic meaning. Similar texts produce nearby vectors.

### Vector database
ChromaDB stores filter vectors persistently in `data/chroma_db`.

### Retrieval
Runtime query vector is compared with stored vectors using cosine similarity to get top-K candidates.

### LLM refinement
LLM is used as a constrained selector/reranker on top retrieved candidates (not open-ended generation).

### Pipeline
This is a staged hybrid pipeline:
- Translation → Retrieval → LLM filtering → Level inference

### Memory
- Persistent memory: Chroma vector store
- Short-term runtime memory: in-process embedding cache (`embeddings_cache`)

### Agents
No autonomous agent loop is implemented. The LLM is used as a bounded function call via prompts.

## 5) File-by-file (foundation files)

### `run.py`
- Entry script.
- Imports config and app.
- Starts Flask server with host/port/debug from config.

### `app/main.py`
- Creates Flask app.
- Enables CORS.
- Registers filter blueprint.
- Adds one-time startup logging in `before_request`.

### `app/config.py`
- Central constants for models, thresholds, ports, paths.
- Used by almost every module.

### `app/routes/filter_routes.py`
- Defines API endpoints:
  - `/health`
  - `/api/filter/analyze-query`
  - `/api/filter/test`
  - `/api/filter/list_embeddings`
- Owns request validation and service invocation.

### `app/models/request_models.py`
- Pydantic request schemas:
  - `FilterQueryOptions`
  - `FilterQueryRequest`

### `app/models/response_models.py`
- Response structure declarations/documentation models.

---

## 6) Why this design is used

This architecture balances:
- **Speed** (vector retrieval)
- **Precision** (LLM refinement)
- **Control** (restricted candidates + JSON parser)
- **Multilingual support** (translation stage)
- **Maintainability** (separated services)

---

Continue with the next part in:
- `/home/runner/work/smart-filter-selector/smart-filter-selector/fille.MD`

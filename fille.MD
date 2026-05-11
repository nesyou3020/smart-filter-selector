# Part 2 — Advanced, Line-by-Line System Understanding

This is the **next part** with deeper internals.

## 1) `app/services/hybrid_selector.py` (main orchestrator)

### Role
Coordinates the full inference flow and returns one unified response.

### Important methods
- `__init__`: creates EmbeddingService, LLMService, LevelDetector, TranslationService
- `is_ready`: checks embeddings loaded
- `select_filters`: main staged pipeline
- `_apply_confidence_threshold`: optional post-filter utility

### `select_filters` step-by-step
1. Read options (`max_filters_per_category`, `min_confidence`) with defaults.
2. **Stage 0:** `detect_and_translate` converts query to English.
3. **Stage 1:** `find_similar_filters` retrieves top semantic candidates.
4. If no candidates: return safe empty output.
5. **Stage 2:** `refine_filters` asks LLM to reduce/select candidates.
6. **Stage 3:** `detect_levels` infers profile levels.
7. Build final response dictionary with stage timings and metadata.

### Design reason
The orchestrator keeps each AI task isolated but combined in one deterministic API flow.

## 2) `app/services/embedding_service.py` (retrieval engine)

### Role
Performs semantic retrieval from precomputed vectors.

### Key internals
- Chroma persistent client initialization.
- In-memory `filter_embeddings` list loaded from Chroma.
- `embeddings_cache` dictionary for repeated query embeddings.
- `clean_query` preprocessing.
- Cosine similarity scoring over all filter vectors.

### Line-level logic patterns
- Tries to ensure stopwords are available (`nltk` resource handling).
- Loads vector records (`metadatas`, `embeddings`) from Chroma collection.
- Caches query embedding by raw query string.
- Preprocesses text before embedding call.
- Ranks by similarity and truncates to configured top-K.

### Design tradeoff
Brute-force cosine search is simple and robust for moderate catalog size.

## 3) `app/services/llm_service.py` (candidate refinement)

### Role
Converts retrieved candidate list into final structured filter selections.

### Key components
- LangChain `PromptTemplate`
- `StructuredOutputParser`
- Ollama LLM client

### Prompt strategy
Prompt explicitly tells model to:
- use only provided candidates
- avoid inventing new filters
- output strict JSON schema

### Why this is critical
It reduces hallucination risk and keeps outputs machine-consumable.

## 4) `app/services/level_detector.py` (secondary inference)

### Role
Predicts levels (experience, language/tool expertise) from query semantics.

### Workflow
1. Load level taxonomy from `data/levels.json`.
2. Build structured-output prompt.
3. Invoke LLM.
4. Parse JSON into deterministic fields.

### Design reason
Separating level detection from filter selection improves modularity and allows independent tuning.

## 5) `app/services/translation_service.py`

### Role
Handles multilingual normalization before retrieval.

### Logic
- Detect language (`langdetect`).
- If non-English, translate (`deep_translator.GoogleTranslator`).
- Return `original_query`, `translated_query`, `detected_language`, confidence.

### Why not LLM translation here?
Using dedicated translation utility is simpler, usually faster, and avoids unnecessary LLM token cost.

## 6) `app/services/ollama_client.py`

### Role
Low-level HTTP client for Ollama API.

### Functions
- `generate_embedding(text)`: POST `/api/embeddings`
- `check_connection()`: GET `/api/tags`

### Benefit
Decouples transport/API details from higher-level business services.

## 7) Utility modules

### `app/utils/filter_loader.py`
- Loads taxonomy JSON once.
- Flattens nested category/subcategory structures into embedding-ready records.

### `app/utils/similarity.py`
- `cosine_similarity` and batch helper.
- Keeps vector math isolated and reusable.

### `app/utils/token_count.py`
- Estimates token usage for prompts.
- Useful for latency/cost/context-window control.

## 8) Data and preprocessing pipeline

### Source taxonomy
- `data/values_with_context.json` (primary)
- `data/values_with_context_mini.json` (small variant)

### Offline embedding build
- `scripts/generate_embeddings.py`
  - reads flattened filter records
  - calls embedding model
  - writes vectors+metadata to ChromaDB

### Runtime dependency
API readiness depends on this precomputed vector store.

## 9) Testing and evaluation flow

### `test/test_queries.py`
- Loads multilingual benchmark set (`test/test_queries.json`).
- Calls API for each query.
- Computes precision/recall/F1 against expected labels.
- Exports results (Excel).

### `test/test_api.py` (+ root `test_api.py`)
- Manual endpoint smoke tests.

This gives both qualitative (manual) and quantitative (metric) validation.

## 10) Deep system relationships map

- `run.py` → imports `app.main` → registers routes.
- Route `/analyze-query` → `HybridFilterSelector.select_filters`.
- `HybridFilterSelector` calls:
  - `TranslationService`
  - `EmbeddingService`
  - `LLMService`
  - `LevelDetector`
- `EmbeddingService` depends on:
  - `OllamaClient` for query embeddings
  - ChromaDB persistent vectors
  - similarity utilities
- `LLMService` and `LevelDetector` both depend on:
  - Ollama LLM via LangChain
  - strict prompt + structured parser patterns

## 11) Advanced AI interpretation of this architecture

This project is a practical **RAG-like selector system** where:
- retrieval corpus = filter taxonomy entries,
- retrieval unit = one filter item,
- reranker/reasoner = LLM with strict schema,
- auxiliary classifier = level detector.

No full document chunking is required because records are already atomic and domain-structured.

## 12) What to improve if scaling further

1. Move config to environment-based settings.
2. Add ANN/vector index optimization for very large filter catalogs.
3. Add robust request/response schema enforcement in routes.
4. Add CI unit+integration tests with deterministic fixtures.
5. Add feedback loop endpoint implementation for continuous quality tuning.

---

If you want, the **next step** can be a strict literal line-by-line annotation of each Python file (every import, class, function, and branch) in sequence.

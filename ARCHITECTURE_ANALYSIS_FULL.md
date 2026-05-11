# Smart Filter Selector — Complete Architectural Analysis

Repository analyzed: `<repository-root>`
Runtime project root: `<repository-root>/smart-filter-selector/smart-filter-selector`

## 1) Project structure and purpose

This repository has a wrapper root plus a nested runtime project:

- Wrapper root contains:
  - `ARCHITECTURE_AND_CONCEPTS.md` (conceptual architecture guide) ([`/home/runner/work/smart-filter-selector/smart-filter-selector/ARCHITECTURE_AND_CONCEPTS.md:1`](/home/runner/work/smart-filter-selector/smart-filter-selector/ARCHITECTURE_AND_CONCEPTS.md:1))
  - `IMPLEMENTATION_GUIDE.md` (adaptation guide for another project) ([`/home/runner/work/smart-filter-selector/smart-filter-selector/IMPLEMENTATION_GUIDE.md:1`](/home/runner/work/smart-filter-selector/smart-filter-selector/IMPLEMENTATION_GUIDE.md:1))
  - nested source directory `smart-filter-selector/smart-filter-selector`

- Runtime root contains service code, data, scripts, tests, container files ([`/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/README.md:68`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/README.md:68)).

A complete file/dir list is provided in `ARCHITECTURE_FILE_TREE.md`.

---

## 2) Core components (Python modules, classes, functions)

## Entrypoints and app composition

- `run.py` starts Flask using `config.FLASK_PORT` and `config.FLASK_DEBUG` ([`.../run.py:1-8`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/run.py:1)).
- `app/main.py` defines `create_app()`, enables CORS, registers `filter_bp`, logs startup metadata ([`.../app/main.py:15-38`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/main.py:15)).
- `app/routes/filter_routes.py` defines API endpoints and initializes service singletons at module load (`HybridFilterSelector`, `OllamaClient`, Chroma client) ([`.../app/routes/filter_routes.py:16-22`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/routes/filter_routes.py:16)).

## Models

- `app/models/request_models.py`
  - `FilterQueryOptions`
  - `FilterQueryRequest`
  - Used for request validation in `analyze_query` ([`.../app/models/request_models.py:8-23`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/models/request_models.py:8), [`.../app/routes/filter_routes.py:46-50`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/routes/filter_routes.py:46)).
- `app/models/response_models.py`
  - `FilterResponse`, `HealthResponse` are defined but not enforced by routes directly ([`.../app/models/response_models.py:6-30`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/models/response_models.py:6)).

## Services (core logic)

- `HybridFilterSelector` orchestrates full pipeline:
  - Stage 0 translation
  - Stage 1 embedding retrieval
  - Stage 2 LLM refinement
  - Stage 3 level detection
  ([`.../app/services/hybrid_selector.py:27-136`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/hybrid_selector.py:27)).

- `EmbeddingService`
  - Initializes Chroma client, loads embeddings into memory, computes cosine similarity, returns top-K candidates
  - Maintains in-process query embedding cache
  ([`.../app/services/embedding_service.py:32-37`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/embedding_service.py:32), [`...:49-70`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/embedding_service.py:49), [`...:72-87`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/embedding_service.py:72), [`...:197-213`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/embedding_service.py:197)).

- `LLMService`
  - Uses LangChain `Ollama`, `PromptTemplate`, `StructuredOutputParser`
  - Prompts model to choose only from retrieved candidates and output strict JSON
  ([`.../app/services/llm_service.py:17-24`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/llm_service.py:17), [`...:26-105`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/llm_service.py:26), [`...:107-144`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/llm_service.py:107)).

- `LevelDetector`
  - Loads level taxonomy from `data/levels.json`
  - Uses a second structured LangChain+Ollama prompt to infer experience/tool/language levels
  ([`.../app/services/level_detector.py:30-42`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/level_detector.py:30), [`...:44-154`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/level_detector.py:44), [`...:156-187`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/level_detector.py:156)).

- `TranslationService`
  - Detects language with `langdetect`
  - Translates non-English queries to English with `deep_translator.GoogleTranslator`
  ([`.../app/services/translation_service.py:16-35`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/translation_service.py:16)).

- `OllamaClient`
  - Calls Ollama embedding endpoint (`/api/embeddings`)
  - Checks connectivity with `/api/tags`
  ([`.../app/services/ollama_client.py:21-31`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/ollama_client.py:21), [`...:33-44`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/ollama_client.py:33)).

## Utilities

- `FilterLoader` loads and flattens both flat and nested filter JSON structures ([`.../app/utils/filter_loader.py:12-53`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/utils/filter_loader.py:12)).
- `similarity.py` provides cosine similarity functions ([`.../app/utils/similarity.py:4-49`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/utils/similarity.py:4)).
- `token_count.py` counts tokens for prompt observability ([`.../app/utils/token_count.py:4-22`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/utils/token_count.py:4)).

## Dependency graph (component-level)

```text
run.py
└─ app.main
   ├─ app.config
   └─ app.routes.filter_routes
      ├─ app.models.request_models
      ├─ app.services.hybrid_selector
      │  ├─ app.services.translation_service
      │  ├─ app.services.embedding_service
      │  │  ├─ app.services.ollama_client
      │  │  └─ app.utils.similarity
      │  ├─ app.services.llm_service
      │  │  └─ app.utils.token_count
      │  └─ app.services.level_detector
      │     └─ app.utils.token_count
      ├─ app.services.ollama_client
      └─ chromadb.PersistentClient
```

---

## 3) AI and ML concepts

## Embeddings

- Model configured: `mxbai-embed-large` ([`.../app/config.py:5`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/config.py:5)).
- Generated via Ollama API (`/api/embeddings`) ([`.../app/services/ollama_client.py:21-31`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/ollama_client.py:21)).
- Offline generation pipeline in `scripts/generate_embeddings.py` embeds flattened filter items and stores into ChromaDB ([`.../scripts/generate_embeddings.py:61-89`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/scripts/generate_embeddings.py:61)).

## Vector DB usage

- ChromaDB persistent client at `data/chroma_db` and collection `filter_embeddings` ([`.../app/config.py:20-21`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/config.py:20)).
- Startup loads Chroma collection embeddings into in-memory `filter_embeddings` list ([`.../app/services/embedding_service.py:56-70`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/embedding_service.py:56)).
- Runtime search is in-process cosine over loaded vectors (not Chroma ANN query) ([`.../app/services/embedding_service.py:197-213`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/embedding_service.py:197)).

## LLMs

- Model configured: `llama3.1:8b` ([`.../app/config.py:6`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/config.py:6)).
- Used through LangChain `Ollama` in `LLMService` and `LevelDetector` ([`.../app/services/llm_service.py:18-24`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/llm_service.py:18), [`.../app/services/level_detector.py:22-28`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/level_detector.py:22)).
- Inference strategy: strict structured JSON parsing with schemas (`StructuredOutputParser`) and deterministic-ish low temperature ([`.../app/services/llm_service.py:28-73`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/llm_service.py:28), [`.../app/services/level_detector.py:46-83`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/level_detector.py:46)).

## Chunking/tokenization

- No document chunking pipeline implemented.
- Query normalization is lexical: accent strip, lowercase, regex cleanup, stopword removal ([`.../app/services/embedding_service.py:104-116`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/embedding_service.py:104)).
- `tiktoken` used for prompt token counting only ([`.../app/utils/token_count.py:4-22`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/utils/token_count.py:4)).

## Retrieval / RAG pattern

- Pattern is hybrid retrieval + LLM reranking:
  1) semantic retrieval (top-K by cosine)  
  2) LLM refinement constrained to candidate set
- Implemented in `HybridFilterSelector.select_filters` + `LLMService.refine_filters` ([`.../app/services/hybrid_selector.py:67-95`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/hybrid_selector.py:67), [`.../app/services/llm_service.py:107-136`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/llm_service.py:107)).

## Agents/pipelines

- No autonomous agent framework.
- Explicit deterministic pipeline orchestrator (`HybridFilterSelector`) with 4 fixed stages ([`.../app/services/hybrid_selector.py:31-35`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/hybrid_selector.py:31)).

## Memory management

- Persistent memory: Chroma persisted embeddings.
- In-process memory: `embeddings_cache` and loaded `filter_embeddings` list in `EmbeddingService` ([`.../app/services/embedding_service.py:34-35`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/embedding_service.py:34)).
- No conversational session memory.

## Prompt engineering

- Strong constraints in prompt templates:
  - output must match parser schema
  - return JSON only
  - do not invent filters/categories
  - only use candidate set
  ([`.../app/services/llm_service.py:88-97`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/llm_service.py:88)).
- Parallel prompt style for level detection with explicit decision guidelines ([`.../app/services/level_detector.py:94-146`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/level_detector.py:94)).

---

## 4) Data flow mapping

## Inbound

- Client sends POST `/api/filter/analyze-query` with `query` and optional options (`maxFiltersPerCategory`, `minConfidence`) ([`.../README.md:53-66`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/README.md:53), [`.../app/routes/filter_routes.py:38-50`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/routes/filter_routes.py:38)).

## Processing chain

1. Request validation with Pydantic (`FilterQueryRequest`)  
   ([`.../app/routes/filter_routes.py:47-50`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/routes/filter_routes.py:47)).
2. Translation stage (`detect_and_translate`)  
   ([`.../app/services/hybrid_selector.py:51-60`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/hybrid_selector.py:51)).
3. Embedding retrieval stage:
   - query cleanup
   - query embedding generation
   - cosine scoring and top-K selection
   ([`.../app/services/embedding_service.py:132-213`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/embedding_service.py:132)).
4. LLM refinement stage over retrieved candidates  
   ([`.../app/services/hybrid_selector.py:90-95`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/hybrid_selector.py:90)).
5. Level detection stage  
   ([`.../app/services/hybrid_selector.py:97-103`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/hybrid_selector.py:97)).
6. Response assembly with timings and stage breakdown  
   ([`.../app/services/hybrid_selector.py:110-133`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/hybrid_selector.py:110)).

## Return path

- JSON response returned by Flask route via `jsonify(result)` ([`.../app/routes/filter_routes.py:68`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/routes/filter_routes.py:68)).

---

## 5) Execution workflows

## Main entry points

- API service startup: `run.py` -> Flask app (`.../run.py`).
- Embedding build: `scripts/generate_embeddings.py`.
- Legacy embedding JSON export: `scripts/generate_embeddings_json.py`.
- Operational bootstrap: `quickstart.sh`.

## Key execution paths

- `/health` checks Ollama connectivity and embeddings availability ([`.../app/routes/filter_routes.py:24-36`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/routes/filter_routes.py:24)).
- `/api/filter/analyze-query` executes full hybrid pipeline ([`.../app/routes/filter_routes.py:38-68`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/routes/filter_routes.py:38)).
- `/api/filter/embeddings` reads embeddings from Chroma collection with request `limit` ([`.../app/routes/filter_routes.py:82-100`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/routes/filter_routes.py:82)).

## State management

- Stateful global service singletons in `filter_routes.py` live for process lifetime.
- `EmbeddingService` keeps runtime cache and loaded vectors in memory.
- No distributed/session store.

## Configuration loading

- Static class values in `app/config.py`; code does not call `os.getenv` or `dotenv` in runtime paths ([`.../app/config.py:2-24`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/config.py:2)).

---

## 6) Architecture patterns, integration, error handling, logging

## Design patterns

- Orchestrator pattern: `HybridFilterSelector` coordinates independent services.
- Service decomposition: translation, retrieval, refinement, level inference separated by class boundaries.
- Gateway/client pattern: `OllamaClient` wraps external inference API.
- Factory-like composition: `create_app()`.

## Integration patterns

- REST API boundary (Flask blueprints).
- Vector persistence boundary (ChromaDB).
- AI inference boundary (Ollama HTTP + LangChain wrapper).
- Translation boundary (Google Translate via deep-translator).

## Error handling

- Route-level broad `try/except`, explicit status codes:
  - 422 invalid request
  - 503 service not ready
  - 500 unhandled error
  ([`.../app/routes/filter_routes.py:49-59`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/routes/filter_routes.py:49), [`...:70-72`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/routes/filter_routes.py:70)).
- Service-level fail-open defaults (empty structures/fallback query) in translation/LLM/level detector.

## Logging and monitoring

- Standard logging configured in app and several services.
- Stage timing emitted in API response (`stages`) and logs.
- Prompt token counts logged for LLM observability.
- No centralized metrics/tracing stack.

---

## 7) Configuration & setup details

## Configuration values

Defined in `app/config.py`:
- Ollama endpoint/models (`OLLAMA_URL`, `OLLAMA_EMBEDDING_MODEL`, `OLLAMA_LLM_MODEL`)
- Flask runtime (`FLASK_PORT`, `FLASK_DEBUG`)
- retrieval thresholds and top-K
- file and DB paths
([`.../app/config.py:2-22`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/config.py:2)).

## Environment variables

- Runtime code currently relies on hardcoded config; no `os.getenv`-based dynamic config in active runtime modules.

## Dependencies

- Declared in `pyproject.toml`, including Flask, LangChain, ChromaDB, deep-translator, langdetect, nltk, tiktoken, pandas/openpyxl ([`.../pyproject.toml:7-25`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/pyproject.toml:7)).

## Setup / initialization

- `quickstart.sh` validates Ollama, pulls required models, installs deps, generates embeddings if missing, then runs service ([`.../quickstart.sh:5-75`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/quickstart.sh:5)).
- `Dockerfile` uses Python slim image, installs with `uv sync`, exposes port 8000, starts `run.py` ([`.../Dockerfile:1-25`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/Dockerfile:1)).

---

## 8) Why this architecture exists (design intent)

- Fast candidate narrowing with embeddings + deterministic refinement with LLM gives quality/speed balance (documented in architecture guide) ([`.../ARCHITECTURE_AND_CONCEPTS.md:321-329`](/home/runner/work/smart-filter-selector/smart-filter-selector/ARCHITECTURE_AND_CONCEPTS.md:321)).
- Translation-first design supports multilingual queries with a single downstream English pipeline ([`.../app/services/hybrid_selector.py:51-65`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/hybrid_selector.py:51)).
- Precomputed persistent embeddings reduce per-request cost and keep runtime simple ([`.../scripts/generate_embeddings.py:23-100`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/scripts/generate_embeddings.py:23)).

---

## 9) Notable mismatches / technical debt observed

- `SOA.md` describes FastAPI while runtime implementation is Flask ([`.../SOA.md:27-31`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/SOA.md:27), [`.../app/main.py:15-23`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/main.py:15)).
- `generate_embeddings_json.py` appears incompatible with current `FilterLoader.flatten_filter_values()` return shape (tuple unpacking vs dict items) ([`.../scripts/generate_embeddings_json.py:49`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/scripts/generate_embeddings_json.py:49), [`.../app/utils/filter_loader.py:31-53`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/utils/filter_loader.py:31)).
- Confidence threshold pipeline hook exists but is currently disabled in `HybridFilterSelector` ([`.../app/services/hybrid_selector.py:104-105`](/home/runner/work/smart-filter-selector/smart-filter-selector/smart-filter-selector/smart-filter-selector/app/services/hybrid_selector.py:104)).


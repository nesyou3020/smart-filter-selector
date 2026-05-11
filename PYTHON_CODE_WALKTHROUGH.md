# Smart Filter Selector — Python Code Walkthrough

Repository root: `<repository-root>`  
Runtime Python project: `<repository-root>/smart-filter-selector/smart-filter-selector`

This document explains the Python codebase in execution order, then breaks the code down file by file. It covers imports, top-level execution, classes, functions, methods, major branches, inputs, outputs, and how data moves between components.

---

## 1. End-to-end workflow: system start to system end

### 1.1 Offline preparation workflow

Before the API can answer queries well, the project expects embeddings to be generated and stored.

1. A developer runs `scripts/generate_embeddings.py`.
2. That script loads the filter taxonomy from `data/values_with_context.json` through `FilterLoader`.
3. It converts each filter entry into an embedding request text.
4. It calls the Ollama embeddings API through `OllamaClient.generate_embedding()`.
5. It stores the embedding vectors plus metadata in ChromaDB under `data/chroma_db`.
6. Later, the API process loads those stored embeddings into memory inside `EmbeddingService`.

That preparation flow is implemented in `scripts/generate_embeddings.py:23-103`, `app/utils/filter_loader.py:12-53`, and `app/services/ollama_client.py:11-31`.

### 1.2 Runtime request workflow

At runtime, the main request path is:

1. `run.py` starts Flask.
2. `app/main.py` creates the Flask application and registers routes.
3. Importing `app.routes.filter_routes` creates long-lived service objects:
   - `HybridFilterSelector`
   - `OllamaClient`
   - Chroma persistent client
4. Creating `HybridFilterSelector` creates:
   - `EmbeddingService`
   - `LLMService`
   - `LevelDetector`
   - `TranslationService`
5. `EmbeddingService` immediately loads stored embeddings from Chroma into `self.filter_embeddings`.
6. A client calls `POST /api/filter/analyze-query`.
7. The route validates the JSON body with Pydantic.
8. The route calls `HybridFilterSelector.select_filters()`.
9. `HybridFilterSelector` executes four stages:
   - translation
   - embedding retrieval
   - LLM refinement
   - level detection
10. The route serializes the result to JSON and returns it.

That full path is defined mainly in `run.py:1-8`, `app/main.py:15-38`, `app/routes/filter_routes.py:16-101`, and `app/services/hybrid_selector.py:27-136`.

### 1.3 Data flow summary

Input data:
- HTTP JSON request containing `query` and optional `options`

Intermediate data:
- translated query text
- query embedding vector
- top similarity candidates
- LLM-selected reduced filters
- detected levels and confidences
- per-stage timings

Output data:
- JSON response containing original and translated query fields, selected filters, confidence, reasoning, detected levels, and timing metrics

---

## 2. Execution order by Python file

### Stage A — application startup

1. `run.py`
2. `app/config.py`
3. `app/main.py`
4. `app/routes/filter_routes.py`
5. `app/services/hybrid_selector.py`
6. `app/services/embedding_service.py`
7. `app/services/ollama_client.py`
8. `app/services/llm_service.py`
9. `app/services/level_detector.py`
10. `app/services/translation_service.py`
11. `app/utils/similarity.py`
12. `app/utils/token_count.py`
13. `app/models/request_models.py`

### Stage B — offline support

14. `app/utils/filter_loader.py`
15. `scripts/generate_embeddings.py`
16. `scripts/generate_embeddings_json.py`

### Stage C — tests and experiments

17. `test_api.py`
18. `test/test_api.py`
19. `test/test_queries.py`
20. `test/test_lang_translation.py`
21. `test/translation_service_llm.py`

### Stage D — package marker files

22. `app/__init__.py`
23. `app/models/__init__.py`
24. `app/routes/__init__.py`
25. `app/services/__init__.py`
26. `app/utils/__init__.py`

These `__init__.py` files are empty package markers. They do not add runtime logic, but they make the directories importable Python packages.

---

## 3. File-by-file walkthrough

## 3.1 `<repository-root>/smart-filter-selector/smart-filter-selector/run.py`

### Role in the system
This is the process entrypoint for the Flask service.

### Imports
- `from app.config import config`  
  Imports the singleton-style configuration object so runtime parameters such as port and debug mode are available.
- `from app.main import app`  
  Imports the Flask app object. Importing this file is important because it triggers creation of the full application object and route registration.

### Top-level execution flow
- Line 4 checks `if __name__ == '__main__':`. This branch ensures the server starts only when the file is executed directly.
- Lines 5-8 call `app.run(...)`.
  - `host='0.0.0.0'` exposes the service to external callers.
  - `port=config.FLASK_PORT` uses the configured port.
  - `debug=config.FLASK_DEBUG` enables Flask debug mode when configured.

### Data in / out
- Input: none directly; it reads config values.
- Output: starts a long-running Flask web process.

### Why it exists
It provides the simplest boot path for local development and container startup.

---

## 3.2 `<repository-root>/smart-filter-selector/smart-filter-selector/app/config.py`

### Role in the system
Centralizes application constants.

### Imports
- No external imports.

### Top-level objects
- `class Config:` stores constants as class attributes.
- `config = Config()` creates an instance used across the project.

### Fields and why each exists
- `OLLAMA_URL`  
  Base URL for both embeddings and LLM inference.
- `OLLAMA_EMBEDDING_MODEL`  
  Embedding model name sent to Ollama.
- `OLLAMA_LLM_MODEL`  
  LLM model name used by LangChain.
- `FLASK_PORT`, `FLASK_DEBUG`  
  Runtime server settings.
- `MIN_CONFIDENCE_THRESHOLD`  
  Planned threshold for post-filtering LLM results.
- `MIN_CONFIDENCE_THRESHOLD_EMBEDDING`  
  Planned threshold for raw embedding matches.
- `TOP_K_SIMILARITY`  
  Number of embedding candidates passed to the LLM.
- `FILTER_CONFIG_PATH`  
  JSON file containing the filter taxonomy.
- `EMBEDDINGS_PATH`  
  Legacy JSON embeddings output path.
- `PERSIST_DIRECTORY`  
  Chroma persistence directory.
- `EMBEDDINGS_COLLECTION_NAME`  
  Chroma collection name.

### Data in / out
- Input: none.
- Output: a shared source of configuration values for all other modules.

### Interaction pattern
Almost every service imports `config`, so this file effectively defines the operating environment of the whole application.

---

## 3.3 `<repository-root>/smart-filter-selector/smart-filter-selector/app/main.py`

### Role in the system
Builds the Flask application object.

### Imports
- `import logging`  
  Used for startup logging.
- `from flask import Flask`  
  Core Flask app class.
- `from flask_cors import CORS`  
  Adds CORS support.
- `from app.config import config`  
  Used only for startup logging values.
- `from app.routes.filter_routes import filter_bp`  
  Imports the blueprint. This import is important because it executes route module top-level initialization.

### Top-level setup
- `logging.basicConfig(...)` sets a global log format.
- `logger = logging.getLogger("smart-filter-selector")` names the logger.

### `create_app()`

#### What it does
Creates a configured Flask app.

#### Step by step
- `app = Flask(__name__)` creates the Flask application.
- `CORS(app, resources={r"/*": {"origins": "*"}})` allows any origin to call the API.
- `app.register_blueprint(filter_bp)` mounts all filter routes.
- Defines `startup()` with `@app.before_request`.
  - This function runs before every request.
  - Branch: `if not hasattr(app, 'startup_done'):` ensures the startup log runs only once.
  - It logs the Ollama URL, LLM model, and embedding model, then sets `app.startup_done = True`.
- Returns the configured app.

### Final line
- `app = create_app()` creates the application at import time.

### Data in / out
- Input: config values and imported blueprint.
- Output: Flask application object with routes and middleware attached.

### Why it is needed
It separates framework assembly from the process entrypoint so the app can be imported by tests, WSGI servers, or other tooling.

---

## 3.4 `<repository-root>/smart-filter-selector/smart-filter-selector/app/models/request_models.py`

### Role in the system
Validates incoming API request payloads.

### Imports
- `Optional` from `typing`  
  Used for optional fields.
- `BaseModel`, `Field` from `pydantic`  
  Used to define structured request schemas.
- `config`  
  Provides default values.

### `FilterQueryOptions`

#### Fields
- `maxFiltersPerCategory` defaults to `config.TOP_K_SIMILARITY`.
- `minConfidence` defaults to `config.MIN_CONFIDENCE_THRESHOLD`.

#### Why it exists
It groups optional tuning parameters so the route can accept one clean `options` object.

### `FilterQueryRequest`

#### Fields
- `query` is required.
- `options` uses `default_factory=FilterQueryOptions`, so missing options are replaced with defaults instead of `None`.

### Data in / out
- Input: raw request JSON.
- Output: typed Python objects with validated values.

### Main branch behavior
- If input does not satisfy the schema, Pydantic raises `ValidationError`, and the route converts that to HTTP 422.

---

## 3.5 `<repository-root>/smart-filter-selector/smart-filter-selector/app/models/response_models.py`

### Role in the system
Defines response schemas for documentation and structure, although the routes return plain dictionaries rather than constructing these models directly.

### Imports
- typing helpers: `Any`, `Dict`, `List`, `Optional`
- Pydantic `BaseModel`, `Field`

### `FilterResponse`

This model describes the shape of the main API response.

#### Translation fields
- `originalQuery`
- `translatedQuery`
- `detectedLanguage`
- `isTranslated`
- `translationConfidence`

#### Filter-selection fields
- `query`
- `reducedFilters`
- `confidence`
- `reasoning`

#### Level-detection fields
- `detectedLevels`
- `levelConfidence`
- `levelReasoning`

#### Timing fields
- `processingTime`
- `totalReduction`
- `stages`

### `HealthResponse`
- `status`
- `ollama_connected`
- `embeddings_loaded`

### Why it exists
It captures intended response contracts even though the rest of the code currently bypasses explicit model serialization.

---

## 3.6 `<repository-root>/smart-filter-selector/smart-filter-selector/app/routes/filter_routes.py`

### Role in the system
Defines the HTTP API surface and translates HTTP requests into service calls.

### Imports
- `logging` for request and error logging.
- `chromadb` and `Settings` to access the persistent vector store from a route.
- `Blueprint`, `jsonify`, `request` from Flask for route definitions and JSON I/O.
- `ValidationError` from Pydantic for request-schema failures.
- `config` for persistence settings.
- `FilterQueryRequest` for request validation.
- `HybridFilterSelector` for the main AI workflow.
- `OllamaClient` for the health check.

### Top-level objects and why they matter
- `filter_bp = Blueprint('filter', __name__)` defines a route group.
- `hybrid_selector = HybridFilterSelector()` builds the core orchestration service at import time.
- `ollama_client = OllamaClient()` builds a lightweight Ollama HTTP client.
- `client_db = chromadb.PersistentClient(...)` prepares a direct Chroma route client.

The import-time construction means the app pays startup cost once, not per request.

### Route: `health_check()`

#### Execution
- Calls `ollama_client.check_connection()`.
- Calls `hybrid_selector.is_ready()`.
- Branch: if both are true, `status` becomes `healthy`; otherwise `unhealthy`.
- Returns JSON with service readiness fields.

#### Data in / out
- Input: no request body.
- Output: service health dictionary.

### Route: `analyze_query()`

#### Execution order
1. `data = request.get_json()` reads the request body.
2. Logs the received payload.
3. Inner validation branch:
   - tries `FilterQueryRequest(**data)`
   - on `ValidationError`, returns `422` with structured errors.
4. Readiness branch:
   - `if not hybrid_selector.is_ready()` returns `503` with instructions to generate embeddings.
5. Calls `hybrid_selector.select_filters(...)` with validated values.
6. Returns `jsonify(result)`.
7. Outer `except Exception` catches unexpected failures and returns `500`.

#### Data in / out
- Input: JSON body with `query` and `options`.
- Output: analysis response from the selector pipeline.

### Route: `test_endpoint()`
- Returns a simple success message and readiness flag.
- Useful for quick manual smoke checks.

### Route: `list_embeddings()`

#### Execution
- Reads request JSON and logs it.
- Reads a collection from Chroma by name.
- Calls `.get(include=["metadatas", "embeddings"], limit=data.get("limit", 10))`.
- Returns a list of dictionaries with id, metadata, and embedding.

#### Important branch
- `embedding.tolist() if hasattr(embedding, "tolist") else embedding` handles both numpy-like and plain Python list values.

### Why this file matters architecturally
It is the boundary between HTTP and the AI pipeline.

---

## 3.7 `<repository-root>/smart-filter-selector/smart-filter-selector/app/services/hybrid_selector.py`

### Role in the system
This is the main orchestrator. It does not perform the low-level AI work itself. Instead, it coordinates specialized services in sequence.

### Imports
- `json` is imported but not used in the active logic.
- `logging` for workflow logs.
- `perf_counter` for stage timing.
- typing helpers.
- `config` for thresholds and top-k.
- `EmbeddingService`, `LevelDetector`, `LLMService`, `TranslationService` for orchestration.

### `HybridFilterSelector.__init__()`
Creates one instance of each major subsystem:
- `EmbeddingService()`
- `LLMService()`
- `LevelDetector()`
- `TranslationService()`

This gives the route layer one object that owns the whole workflow.

### `is_ready()`
- Calls `self.embedding_service.is_loaded()`.
- Returns `True` only if embeddings are already loaded into memory.

### `select_filters(query, max_filters=None, min_confidence=None)`

This is the single most important method in the project.

#### Initial normalization
- Starts a timer with `perf_counter()`.
- Resolves defaults:
  - `max_filters = max_filters or config.TOP_K_SIMILARITY`
  - `min_confidence = min_confidence or config.MIN_CONFIDENCE_THRESHOLD`
- Logs the raw input query.

#### Stage 0: translation
- Calls `self.translation_service.detect_and_translate(query)`.
- Stores stage timing.
- Extracts:
  - `translated_query`
  - `detected_language`
  - `is_translated`
  - `translation_conf`
- Logs the translation result.

#### Stage 1: embedding retrieval
- Calls `self.embedding_service.find_similar_filters(translated_query)`.
- Stores stage timing.
- Logs candidate count.

#### Branch: no candidates
If no candidates are found, it returns immediately with:
- original and translated query data
- empty `reducedFilters`
- empty `confidence`
- reasoning error message
- total processing time

This branch prevents downstream LLM calls when retrieval cannot produce inputs.

#### Stage 2: LLM refinement
- Calls `self.llm_service.refine_filters(translated_query, candidates, max_filters)`.
- Stores stage timing.
- Logs completion.

#### Stage 3: level detection
- Calls `self.level_detector.detect_levels(translated_query)`.
- Stores stage timing.
- Logs completion.

#### Threshold branch
- `_apply_confidence_threshold(...)` exists but is commented out.
- So `min_confidence` is accepted from callers but not actively applied to the final result.

#### Final assembly
Returns a dictionary containing:
- translation metadata
- `reducedFilters`
- raw `embedding_search_candidates`
- confidence and reasoning from the LLM
- detected levels from the level detector
- total processing time
- per-stage timing map

### `_apply_confidence_threshold(result, min_confidence)`

This helper is currently dormant but still important to understand.

#### Purpose
Filter out low-confidence categories or subcategories.

#### Main branches
- Iterates through each category in `reducedFilters`.
- Branch 1: if `cat_confidence` is a dict, it treats the category as hierarchical.
  - Iterates through subcategories.
  - Converts subcategory confidence to float.
  - Keeps only subcategories whose confidence is at least `min_confidence`.
- Branch 2: if confidence is scalar, it treats the category as flat.
  - Keeps or drops the whole category.
- On any failure, it logs the error and falls back to unfiltered results.

### Data in / out
- Input: user query plus optional tuning parameters.
- Output: a large result dictionary ready for HTTP serialization.

### Why this file matters
It expresses the project’s architecture directly: translation first, retrieval second, reasoning third, skill-level inference fourth.

---

## 3.8 `<repository-root>/smart-filter-selector/smart-filter-selector/app/services/embedding_service.py`

### Role in the system
Loads and searches embeddings.

### Imports
- `json` is imported but not used in the active path.
- `logging`, `os`, `re`, `unicodedata` for logs, filesystem checks, regex cleaning, and accent normalization.
- typing helpers.
- `nltk` and `stopwords` for stopword filtering.
- `PersistentClient`, `Settings` from ChromaDB.
- `config` for persistence paths and top-k.
- `OllamaClient` for query embedding generation.
- `cosine_similarity` for vector scoring.

### Top-level branch: stopword bootstrap
- It tries `stopwords.words("english")`.
- If NLTK data is missing, it downloads the stopwords corpus.

This means the first startup may trigger a quiet resource download.

### `__init__()`
- Creates an `OllamaClient`.
- Initializes `embeddings_cache = {}`.
- Initializes `filter_embeddings = []`.
- Creates a Chroma client by calling `_init_chroma()`.
- Calls `load_embeddings()` immediately.

### `is_loaded()`
- Returns `len(self.filter_embeddings) > 0`.
- This is the readiness condition used by the API layer.

### `_init_chroma()`
- Builds `PersistentClient(path=config.PERSIST_DIRECTORY, settings=Settings(anonymized_telemetry=False))`.
- Logs a success message.
- Returns the client.

### `load_embeddings()`

#### Purpose
Load all stored embedding rows from Chroma into Python memory.

#### Branches
- If `config.PERSIST_DIRECTORY` does not exist:
  - logs warnings
  - returns early
- Otherwise:
  - reads the configured collection from Chroma
  - calls `.get(include=["metadatas", "embeddings"])`
  - converts the raw Chroma result into a list of normalized dictionaries with:
    - category
    - subcategory
    - name
    - description
    - embedding
  - stores that list in `self.filter_embeddings`

#### Why it exists
Runtime search becomes simple in-memory cosine scoring instead of repeated database calls.

### `get_query_embedding(query)`

#### Purpose
Avoid duplicate embedding requests.

#### Branches
- Cache hit: return cached vector.
- Cache miss: call Ollama, store result in cache, return it.

### `clean_query(query)`

#### Purpose
Normalize text before embedding lookup.

#### Step by step
- Normalizes accents to ASCII.
- Lowercases the string.
- Removes non-letter characters and digits with `re.sub(r"[^a-z\s]", " ", ...)`.
- Splits into words.
- Filters out English stopwords.
- Filters out very short words (`len(w) > 2`).
- Joins the remaining tokens.

#### Data effect
A sentence like a multilingual natural query becomes a compressed bag-of-words-like string, which may change semantic quality but reduces noise.

### `find_similar_filters(query)`

#### Purpose
Retrieve the most relevant filter candidates by vector similarity.

#### Branches and flow
1. If no embeddings are loaded:
   - logs a warning
   - returns `{}`
2. Cleans the query text.
3. Logs the cleaned query.
4. Calls `get_query_embedding(cleaned_query)`.
5. Iterates over every item in `self.filter_embeddings`.
6. For each item, computes cosine similarity between query vector and stored embedding.
7. Builds a dictionary with:
   - `category`
   - `subcategory`
   - `name`
   - `score`
8. Sorts the whole list descending by score.
9. Returns the top `config.TOP_K_SIMILARITY` items.

#### Important design note
There is commented-out code showing an earlier grouped-by-category retrieval design. The active logic now returns one flat top-K list across all categories.

### Data in / out
- Input: translated query string.
- Output: top-K candidate list of filter dictionaries.

### Why it is needed
It cheaply narrows a large filter space into a smaller candidate set before the LLM makes semantic decisions.

---

## 3.9 `<repository-root>/smart-filter-selector/smart-filter-selector/app/services/llm_service.py`

### Role in the system
Refines retrieved candidates with an LLM and forces structured output.

### Imports
- `json`, `logging`, typing helpers.
- `Ollama` from LangChain to call the local LLM.
- `ResponseSchema`, `StructuredOutputParser` to force JSON shape.
- `PromptTemplate` to build the prompt.
- `config` for model settings.
- `count_tokens` for prompt observability.

### `__init__()`
- Builds a LangChain `Ollama` client with:
  - base URL from config
  - model from config
  - temperature `0.15`
  - `num_gpu=1`
- Calls `setup_chain()`.

### `setup_chain()`

#### Purpose
Defines the structured response contract and the full selection prompt.

#### Response schemas
- `reducedFilters`
- `confidence`
- `reasoning`

#### Prompt behavior
The prompt tells the model to:
- analyze the user query
- choose only from the retrieved candidates
- provide confidence per category
- explain reasoning
- output strict JSON only
- avoid inventing filters or categories

#### Final object graph
- `self.output_parser` parses the expected JSON.
- `self.prompt` is a `PromptTemplate`.
- `self.chain = self.prompt | self.llm | self.output_parser` creates a LangChain pipeline.

### `refine_filters(query, candidates, max_per_category)`

#### Flow
1. Calls `_format_candidates(candidates, max_per_category)`.
2. Renders the prompt for logging and token counting.
3. Logs prompt token count.
4. Invokes `self.chain` with query and candidate string.
5. Returns parsed JSON output.

#### Error branch
If the LLM call or parsing fails, it logs an error and returns empty structures.

#### Important note
`max_per_category` is accepted but `_format_candidates()` currently ignores it. So the parameter is part of the API surface but not applied inside candidate formatting.

### `_format_candidates(candidates, max_per_category)`
- Converts each candidate into a smaller dict with only:
  - `name`
  - `category`
  - `subcategory`
- Serializes the result to JSON.
- It intentionally omits embedding similarity score and description from the prompt payload.

### Data in / out
- Input: translated query and flat candidate list.
- Output: structured LLM decision dictionary.

### Why it is needed
Embedding search finds semantically nearby items, but the LLM is used as a higher-level reasoning layer to choose which candidates best fit the actual user intent.

---

## 3.10 `<repository-root>/smart-filter-selector/smart-filter-selector/app/services/level_detector.py`

### Role in the system
Runs a second LLM task focused on level inference rather than filter selection.

### Imports
- `json`, `logging`, `os`, typing helpers, `re`.
- LangChain `Ollama`, `ResponseSchema`, `StructuredOutputParser`, `PromptTemplate`.
- `config` for model settings.
- `count_tokens` for prompt logging.

### `__init__()`
- Loads available levels using `_load_levels()`.
- Builds an Ollama LLM client.
- Calls `setup_chain()`.

### `_load_levels()`

#### Purpose
Load the available level taxonomy.

#### Branches
- Success branch:
  - opens `data/levels.json`
  - parses JSON and returns it
- Failure branch:
  - logs a warning-style info message
  - returns a hardcoded fallback taxonomy:
    - language-level
    - experience
    - tool-expertise

### `setup_chain()`

#### Purpose
Defines the structured prompt for level detection.

#### Schemas
- `detectedLevels`
- `confidence`
- `reasoning`

#### Prompt logic
The prompt instructs the LLM to infer:
- overall seniority
- tool expertise
- language level only when explicitly mentioned

It includes detailed guidelines for explicit and implicit inference and requires strict JSON.

### `detect_levels(query)`

#### Flow
1. Serializes `self.levels_data` to JSON.
2. Renders the prompt for token counting.
3. Logs prompt token count.
4. Invokes the LangChain chain.
5. Returns the parsed result.

#### Error branch
On failure, returns empty dictionaries for all outputs.

### Data in / out
- Input: translated query text.
- Output: inferred level categories, confidence scores, and reasoning.

### Why it exists
It isolates a separate inference concern so filter selection and level detection can evolve independently.

---

## 3.11 `<repository-root>/smart-filter-selector/smart-filter-selector/app/services/translation_service.py`

### Role in the system
Provides lightweight language detection and translation before all downstream processing.

### Imports
- `logging`
- `Dict` from `typing`
- `GoogleTranslator` from `deep_translator`
- `DetectorFactory`, `detect` from `langdetect`
- `config` is imported but not used in the active code

### Top-level behavior
- `DetectorFactory.seed = 0` makes language detection deterministic across runs.

### `__init__()`
- Creates `GoogleTranslator(source='auto', target='en')`.

### `detect_and_translate(query)`

#### Main flow
1. Calls `detect(query)`.
2. Computes `is_translated = lang != 'en'`.
3. Branch:
   - if non-English, translates with GoogleTranslator
   - otherwise reuses the original query
4. Returns a dictionary with:
   - `detectedLanguage`
   - `translatedQuery`
   - `originalQuery`
   - `confidence`
   - `isTranslated`

#### Error branch
If anything fails, it logs the error and returns a safe fallback using the original query.

### Data in / out
- Input: raw user query in any language.
- Output: normalized English query plus metadata.

### Why it is needed
The embedding and LLM stages are designed around an English-centric downstream workflow, so this service standardizes the text first.

---

## 3.12 `<repository-root>/smart-filter-selector/smart-filter-selector/app/services/ollama_client.py`

### Role in the system
Wraps low-level HTTP calls to Ollama.

### Imports
- `List` typing helper.
- `requests` for HTTP.
- `config` for endpoint and model names.

### `generate_embedding(text)`

#### Step by step
- Builds URL: `f"{config.OLLAMA_URL}/api/embeddings"`.
- Builds payload with:
  - model name
  - prompt text
  - `use_gpu=True`
- Sends `requests.post(...)`.
- Calls `response.raise_for_status()` so non-200 responses become exceptions.
- Returns `response.json()["embedding"]`.

#### Data in / out
- Input: text string.
- Output: embedding vector list of floats.

### `check_connection()`
- Sends `GET /api/tags` with a 5-second timeout.
- Returns `True` if status code is 200.
- Returns `False` on any exception.

### Why it is needed
It keeps HTTP details out of higher-level services.

---

## 3.13 `<repository-root>/smart-filter-selector/smart-filter-selector/app/utils/filter_loader.py`

### Role in the system
Loads the filter taxonomy and normalizes it into a flat structure.

### Imports
- `json`
- typing helpers

### `FilterLoader.__init__(config_path)`
- Stores the config path.
- Sets `self.filter_data = None` for lazy loading.

### `load_filters()`

#### Branches
- If `self.filter_data` is `None`, it opens the JSON file and caches the parsed object.
- Otherwise it returns the cached data.

This avoids repeated file reads.

### `flatten_filter_values()`

#### Purpose
Turn nested filter data into a uniform list for embedding generation.

#### Flow
1. Initializes `flattened = []`.
2. Loads the filter JSON.
3. Iterates `for category, items in filters.items():`.
4. Branch 1: `items` is a list.
   - Treats it as a flat category.
   - Appends one dictionary per item.
5. Branch 2: `items` is a dict.
   - Treats it as hierarchical.
   - Iterates `subcategory, subitems`.
   - Appends one dictionary per nested item.
6. Returns the flat list.

#### Output shape
Each row looks like:
- `name`
- `description`
- `category`
- `subcategory`

### Why it is needed
The raw taxonomy can be nested or flat, but the embedding pipeline wants a uniform record list.

---

## 3.14 `<repository-root>/smart-filter-selector/smart-filter-selector/app/utils/similarity.py`

### Role in the system
Provides cosine-similarity math utilities.

### Imports
- `numpy as np`
- `List` typing helper

### `cosine_similarity(vec_a, vec_b)`

#### Flow
- Converts both vectors to numpy arrays.
- Computes dot product.
- Computes norms of each vector.
- Branch: if either norm is zero, returns `0.0` to avoid division by zero.
- Otherwise returns `dot_product / (norm_a * norm_b)`.

### `batch_cosine_similarity(query_vec, vectors)`

#### Flow
- Converts inputs to numpy arrays.
- Computes all dot products at once.
- Computes vector norms.
- Replaces zero norms with `1e-10`.
- Returns all similarities as a Python list.

### Usage note
Only `cosine_similarity()` is used in the active retrieval path. `batch_cosine_similarity()` is available for future vectorization work.

---

## 3.15 `<repository-root>/smart-filter-selector/smart-filter-selector/app/utils/token_count.py`

### Role in the system
Estimates prompt size before LLM calls.

### Imports
- `tiktoken`

### `count_tokens(text, model='gpt-4-turbo')`

#### Flow
- Tries `tiktoken.encoding_for_model(model)`.
- Branch: if the tokenizer is unknown, falls back to `cl100k_base`.
- Encodes the text.
- Returns token count.

### Why it exists
The service logs prompt sizes for observability and prompt-cost awareness, even though the actual model is Ollama rather than OpenAI.

---

## 3.16 `<repository-root>/smart-filter-selector/smart-filter-selector/scripts/generate_embeddings.py`

### Role in the system
Creates the production embedding store in ChromaDB.

### Imports
- `logging`, `os`, `sys`, `uuid`
- `chromadb`, `Settings`
- `tqdm` for progress bars
- Project imports: `config`, `OllamaClient`, `FilterLoader`

### Top-level path mutation
- `sys.path.insert(...)` adds the project root so the script can import `app.*` modules when executed directly.

### `generate_embeddings()`

#### Step by step
1. Logs that generation is starting.
2. Builds `FilterLoader` and `OllamaClient`.
3. Checks Ollama connection.
   - Branch: on failure, logs error and returns.
4. Loads flattened filters.
   - Branch: on failure, logs error and returns.
5. Creates the persistence directory with `os.makedirs(..., exist_ok=True)`.
6. Creates a Chroma persistent client.
7. Gets or creates the configured collection.
8. Iterates over every flattened filter entry with `tqdm`.
9. For each entry:
   - extracts name, description, category, subcategory
   - builds a structured embedding prompt text
   - calls `ollama_client.generate_embedding(...)`
   - creates safe string metadata
   - stores embedding + metadata + description in Chroma
10. Branch: if one embedding request fails, logs a warning and continues.
11. Logs completion summary.

### Data in / out
- Input: JSON taxonomy plus Ollama service.
- Output: persisted Chroma collection.

### Why it is needed
Without this script, `EmbeddingService` has no vector database to load.

---

## 3.17 `<repository-root>/smart-filter-selector/smart-filter-selector/scripts/generate_embeddings_json.py`

### Role in the system
Legacy alternative embedding-generation script that writes a JSON file instead of ChromaDB.

### Key difference from the active script
Instead of storing into Chroma, it builds `embeddings_data` and writes it to `config.EMBEDDINGS_PATH`.

### Important logic note
This script expects `flattened_filters` rows to unpack as `(category, subcategory, value)`, but the active `FilterLoader.flatten_filter_values()` now returns dictionaries. That means this script no longer matches the current loader contract.

### Branches
- Ollama connection failure → log and return.
- Filter-load failure → log and return.
- Per-item embedding failure → log warning and continue.
- Save failure → log error and return.

### Why it still matters
It documents an earlier design phase where embeddings were stored as JSON rather than in a vector database.

---

## 3.18 `<repository-root>/smart-filter-selector/smart-filter-selector/test_api.py`

### Role in the system
Manual API smoke test script at repository runtime root.

### Imports
- `requests`, `json`, `logging`

### Global
- `BASE_URL = "http://localhost:8000"`

### `test_health()`
- Calls `GET /health`.
- Logs status and parsed JSON.
- Returns `True` if HTTP 200.

### `test_query(query_text, max_filters=10, min_confidence=0.6)`

#### Flow
- Logs the query.
- Builds the request payload.
- Calls `POST /api/filter/analyze-query`.
- Branch: if status 200:
  - logs query and processing time
  - logs stage timings if present
  - iterates over `reducedFilters`
  - handles both list and dict response shapes
  - logs reasoning
- Else:
  - logs the error response body
- Returns success boolean.

### `run_all_tests()`
- Prints a startup banner.
- Calls `test_health()`.
- Branch: if health fails, logs and returns.
- Iterates through six hardcoded domain queries and calls `test_query()`.
- Logs completion.

### Why it exists
It provides a quick human-readable test harness for a running local service.

---

## 3.19 `<repository-root>/smart-filter-selector/smart-filter-selector/test/test_api.py`

This file is effectively a duplicate of `test_api.py` with the same imports, functions, branches, and behavior. It exists as a second copy under the `test/` folder.

---

## 3.20 `<repository-root>/smart-filter-selector/smart-filter-selector/test/test_queries.py`

### Role in the system
Runs many end-to-end API evaluations and computes retrieval quality metrics.

### Imports
- `json`, `logging`
- `SequenceMatcher` for fuzzy string similarity
- `DataFrame` from pandas for Excel export
- `requests` for API calls

### `similar(a, b)`
- Lowercases both strings.
- Computes a similarity ratio.
- Rounds to two decimals.

### `compare_filters(detected, expected)`

#### Purpose
Classifies detected filters as true positives, false positives, and false negatives.

#### Flow
1. Initializes `tp`, `fp`, `fn`.
2. Normalizes whitespace/case in both detected and expected lists.
3. For each expected filter:
   - if any detected filter is at least 0.9 similar, add to `tp`
   - else add to `fn`
4. For each detected filter:
   - if it does not closely match any expected filter, add to `fp`
5. Returns both the lists and their counts.

### `precision_recall_f1(detected, expected)`
- Calls `compare_filters(...)`.
- Computes precision, recall, and F1.
- Branches protect against division by zero.
- Returns rounded metric values.

### `main()`

#### Flow
1. Initializes `results = []`.
2. Opens `test/test_queries.json`.
3. Logs the number of test cases.
4. Iterates over test cases.
5. For each test:
   - posts the query to `/api/filter/analyze-query`
   - branch: if non-200, logs error and continues
   - parses response JSON
   - builds `detected_filters` from names and non-empty subcategories in `reducedFilters`
   - computes precision, recall, F1
   - computes response time by summing stage durations
   - appends a structured result row
   - logs the metrics
6. Branch: any exception per test is logged and the loop continues.
7. Returns `results`.

### `if __name__ == '__main__':`
- Calls `main()`.
- Branch: if results exist:
  - computes average metrics
  - logs summary report
  - exports Excel to `test/test_queries_results.xlsx`
- Else logs that no valid responses were tested.

### Why it exists
It provides a measurable evaluation loop for the end-to-end AI system.

---

## 3.21 `<repository-root>/smart-filter-selector/smart-filter-selector/test/test_lang_translation.py`

### Role in the system
Manual translation smoke test.

### Imports
- `sys`, `os` for path injection
- `TranslationService`
- `logging`

### Top-level behavior
This file does not define functions. It runs immediately when executed.

#### Flow
1. Inserts project root into `sys.path`.
2. Creates logger configuration.
3. Defines `query_examples` list with English, French, and Portuguese examples.
4. Instantiates `TranslationService()`.
5. Loops through each query.
6. Calls `detect_and_translate(query)`.
7. Logs original query, detected language, translated query, confidence, and translation flag.

### Why it exists
It is a quick executable script for visually verifying multilingual preprocessing behavior.

---

## 3.22 `<repository-root>/smart-filter-selector/smart-filter-selector/test/translation_service_llm.py`

### Role in the system
Experimental alternative translation implementation using an LLM instead of `deep_translator`.

### Imports
- `logging`, `re`, `unicodedata`, typing helper `Dict`
- LangChain Ollama stack
- `langdetect`
- `config`

### Top-level behavior
- `DetectorFactory.seed = 0` makes detection deterministic.
- `logger = logging.getLogger(__name__)`

### `TranslationService.__init__()`
- Builds an Ollama LLM client.
- Calls `setup_chain()`.

### `setup_chain()`
- Defines structured response schemas for:
  - `detectedLanguage`
  - `translatedQuery`
  - `confidence`
  - `isTranslated`
- Builds a translation prompt that preserves technical terms and mixed-language behavior.
- Builds `self.chain` as prompt → LLM → parser.

### `detect_and_translate(query)`

#### Flow
1. Fast-path branch: if `_is_likely_english(query)` is true, return the original query without using the LLM.
2. Else invoke the chain with the query.
3. Add `originalQuery` to the structured response.
4. Return the result.

#### Error branch
On failure, log the error and return a fallback result.

### `_is_likely_english(query)`
- Calls `detect(query)`.
- Returns `True` only if detected code is `en`.
- Returns `False` on any exception.

### Why it matters
It shows an alternate design direction: translation as another structured LLM task rather than as a third-party translation API call.

---

## 3.23 Empty package files

The following files are empty and only mark packages:
- `<repository-root>/smart-filter-selector/smart-filter-selector/app/__init__.py`
- `<repository-root>/smart-filter-selector/smart-filter-selector/app/models/__init__.py`
- `<repository-root>/smart-filter-selector/smart-filter-selector/app/routes/__init__.py`
- `<repository-root>/smart-filter-selector/smart-filter-selector/app/services/__init__.py`
- `<repository-root>/smart-filter-selector/smart-filter-selector/app/utils/__init__.py`

They contribute package structure but no runtime branches or data flow.

---

## 4. How all components interact together

## 4.1 Request-processing chain

- Flask route layer receives HTTP JSON.
- Pydantic converts that JSON into a validated Python object.
- `HybridFilterSelector` acts as the orchestrator.
- `TranslationService` standardizes the query language.
- `EmbeddingService` converts the query to a vector and retrieves similar filter candidates.
- `LLMService` chooses the best filters from that candidate set.
- `LevelDetector` independently infers skill/proficiency levels.
- The route returns the combined result.

## 4.2 Storage and model dependencies

- ChromaDB stores precomputed filter vectors.
- Ollama serves both embeddings and LLM inference.
- `deep_translator` provides translation.
- `langdetect` provides language identification.
- `nltk` provides stopwords for lexical cleanup.
- `tiktoken` provides token counting for prompt observability.

## 4.3 Why the architecture is layered this way

The project uses a hybrid AI architecture:
- deterministic HTTP boundary
- deterministic preprocessing
- vector retrieval for fast candidate reduction
- LLM reasoning for semantic refinement
- separate LLM reasoning for level inference

That separation makes the system easier to debug because each stage has a clear responsibility and its own data product.

---

## 5. Important branches and edge cases across the project

### Readiness branches
- No Chroma directory → embeddings are considered missing.
- No loaded embeddings → API returns 503 or empty candidate fallback.

### Translation fallback
- If language detection or translation fails, the original query is still processed.

### Retrieval fallback
- If no candidates are found, the pipeline returns early and skips the LLM stages.

### LLM fallback
- If filter refinement fails, empty results are returned.
- If level detection fails, empty level dictionaries are returned.

### Metric safety branches
- Precision/recall/F1 calculations guard against zero division.

### Serialization branch
- Embedding listing handles both array-like objects and plain lists.

---

## 6. Practical mental model of the codebase

If you want to think about the codebase like a software engineer and AI architect, the simplest mental model is:

- `run.py` starts the process.
- `app/main.py` assembles the web app.
- `filter_routes.py` is the HTTP boundary.
- `hybrid_selector.py` is the workflow brain.
- `translation_service.py` normalizes language.
- `embedding_service.py` narrows the search space.
- `llm_service.py` performs semantic selection.
- `level_detector.py` performs semantic level inference.
- `ollama_client.py` is the low-level AI transport layer.
- `filter_loader.py` and scripts prepare the offline vector memory.
- test files exercise the system from the outside.

That is the full system from beginning to end.

# Step-by-Step Implementation Guide: Intelligent Filter for RBC Log Analyzer

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Phase 1: Setup & Infrastructure](#phase-1-setup--infrastructure)
3. [Phase 2: Data Preparation](#phase-2-data-preparation)
4. [Phase 3: Backend Implementation](#phase-3-backend-implementation)
5. [Phase 4: Frontend Integration](#phase-4-frontend-integration)
6. [Phase 5: Testing & Optimization](#phase-5-testing--optimization)

---

## Project Overview

### Current Situation
- You have an RBC Log Analyzer with an **events/messages filtering system**
- Currently: Users manually select from checkbox lists
- Goal: Add intelligent AI-based filtering like Smart Filter Selector

### What We're Building
```
User Input: "Show me all authentication errors from the last hour"
                            ↓
                    [Intelligent Filter Backend]
                            ↓
Result: Automatically suggests & applies relevant filters
- Event Type: Authentication Error ✓
- Time Range: Last 1 hour ✓
- Severity: High ✓
```

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    RBC Log Analyzer                          │
│                                                               │
│  Frontend (TypeScript/React)                                 │
│  ├─ Query Input Field                                       │
│  └─ Filter Display Component                                │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Backend (Python/Flask) - NEW                               │
│  ├─ Embedding Generation Service                            │
│  ├─ Smart Filter Selector Service                           │
│  ├─ REST API Endpoints                                      │
│  └─ Vector Database (ChromaDB)                              │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Data Storage                                                │
│  ├─ Vector Database (embeddings for all filters)            │
│  └─ Original Filter Definitions                             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Setup & Infrastructure

### Step 1.1: Install Prerequisites

You need to install Ollama (local AI runtime) which provides embeddings and LLM capabilities.

**For Windows/Mac/Linux:**
1. Download Ollama from https://ollama.ai
2. Install and run the application
3. In terminal, pull the required models:

```bash
# Embedding model (for semantic search)
ollama pull mxbai-embed-large

# LLM model (for intelligent refinement)
ollama pull llama2
# or better:
ollama pull mistral
```

Verify Ollama is running:
```bash
curl http://localhost:11434/api/tags
# Should return a JSON with available models
```

### Step 1.2: Create Backend Directory Structure

In your RBC Log Analyzer project, create the backend structure:

```
your-rbc-analyzer/
├── frontend/                    # (existing TypeScript/React)
│   ├── src/
│   │   └── pages/
│   │       └── events/          # Your events page
│   └── ...
│
├── backend/                     # (NEW - we're creating this)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py            # Configuration
│   │   ├── main.py              # Flask app setup
│   │   ├── models/              # Pydantic models
│   │   │   ├── __init__.py
│   │   │   └── request_models.py
│   │   ├── services/            # Core services
│   │   │   ├── __init__.py
│   │   │   ├── embedding_service.py
│   │   │   ├── filter_selector.py
│   │   │   ├── ollama_client.py
│   │   │   └── translation_service.py
│   │   ├── routes/              # API endpoints
│   │   │   ├── __init__.py
│   │   │   └── filter_routes.py
│   │   └── utils/               # Utilities
│   │       ├── __init__.py
│   │       ├── similarity.py
│   │       └── filter_loader.py
│   ├── data/
│   │   ├── filters_config.json  # Your filter definitions
│   │   └── chroma_db/           # Vector database (created later)
│   ├── scripts/
│   │   ├── __init__.py
│   │   └── generate_embeddings.py
│   ├── run.py                   # Entry point
│   ├── requirements.txt
│   └── pyproject.toml
```

### Step 1.3: Create Python Virtual Environment

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Step 1.4: Install Python Dependencies

Create `backend/requirements.txt`:

```txt
Flask==2.3.0
Flask-CORS==4.0.0
Pydantic==2.0.0
requests==2.31.0
chromadb==0.4.0
langchain==0.1.0
ollama==0.1.0
langdetect==1.0.9
deep-translator==1.11.4
numpy==1.24.0
python-dotenv==1.0.0
```

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## Phase 2: Data Preparation

### Step 2.1: Extract Your Current Filters

First, you need to document all the filters you currently have in your RBC Log Analyzer events page.

**Example of what to collect:**

```json
{
  "filters": [
    {
      "category": "Event Type",
      "subcategory": "Authentication",
      "name": "Login Success",
      "description": "Successful user authentication events"
    },
    {
      "category": "Event Type",
      "subcategory": "Authentication",
      "name": "Login Failure",
      "description": "Failed authentication attempts"
    },
    {
      "category": "Event Type",
      "subcategory": "Transaction",
      "name": "Transaction Initiated",
      "description": "Transaction processing started"
    },
    {
      "category": "Severity",
      "subcategory": "",
      "name": "Critical",
      "description": "Critical severity - immediate action required"
    },
    {
      "category": "Severity",
      "subcategory": "",
      "name": "High",
      "description": "High severity - requires attention"
    },
    {
      "category": "Severity",
      "subcategory": "",
      "name": "Medium",
      "description": "Medium severity - should be reviewed"
    },
    {
      "category": "Time Range",
      "subcategory": "",
      "name": "Last 1 Hour",
      "description": "Events from the last 60 minutes"
    },
    {
      "category": "Time Range",
      "subcategory": "",
      "name": "Last 24 Hours",
      "description": "Events from the last day"
    }
  ]
}
```

Create `backend/data/filters_config.json` with your actual filters.

### Step 2.2: Create the Filter Configuration Loader

Create `backend/app/utils/filter_loader.py`:

```python
import json
import os
from typing import List, Dict, Any

class FilterLoader:
    """Load and manage filter configurations."""
    
    def __init__(self, config_path: str):
        """
        Initialize filter loader.
        
        Args:
            config_path: Path to filters_config.json
        """
        self.config_path = config_path
        self.filters = self._load_filters()
    
    def _load_filters(self) -> Dict[str, Any]:
        """Load filter configuration from JSON file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Filter config not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_all_filters(self) -> List[Dict[str, Any]]:
        """Get all filters."""
        return self.filters.get('filters', [])
    
    def get_filters_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get filters by category."""
        return [
            f for f in self.get_all_filters()
            if f.get('category') == category
        ]
    
    def flatten_filter_values(self) -> List[Dict[str, Any]]:
        """
        Flatten filters for embedding generation.
        
        Returns a list of filter items with full context.
        """
        flattened = []
        for filter_item in self.get_all_filters():
            flattened.append({
                'name': filter_item.get('name', ''),
                'category': filter_item.get('category', ''),
                'subcategory': filter_item.get('subcategory', ''),
                'description': filter_item.get('description', '')
            })
        return flattened
    
    def reload(self):
        """Reload filters from file (useful for development)."""
        self.filters = self._load_filters()
```

### Step 2.3: Understand Your Filter Structure

Look at your RBC Log Analyzer events page and list all available filters:

**Example from a typical events page:**

```
┌─ Event Type
│  ├─ Authentication
│  │  ├─ Login Success
│  │  └─ Login Failure
│  ├─ Transaction
│  │  ├─ Transaction Initiated
│  │  └─ Transaction Completed
│  └─ Error
│     ├─ System Error
│     └─ User Error
│
├─ Severity
│  ├─ Critical
│  ├─ High
│  ├─ Medium
│  └─ Low
│
├─ Source
│  ├─ Web Portal
│  ├─ Mobile App
│  └─ API
│
└─ Time Range
   ├─ Last 1 Hour
   ├─ Last 24 Hours
   ├─ Last 7 Days
   └─ Custom Range
```

Document this in `filters_config.json`.

---

## Phase 3: Backend Implementation

### Step 3.1: Configuration Setup

Create `backend/app/config.py`:

```python
import os

class Config:
    """Application configuration."""
    
    # Ollama Configuration
    OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    OLLAMA_EMBEDDING_MODEL = 'mxbai-embed-large'
    OLLAMA_LLM_MODEL = 'mistral'  # or 'llama2'
    
    # Flask Configuration
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', False)
    
    # Application Configuration
    MIN_CONFIDENCE_THRESHOLD = 0.8
    TOP_K_SIMILARITY = 20  # Number of candidates from embedding search
    
    # File Paths
    FILTER_CONFIG_PATH = os.path.join('data', 'filters_config.json')
    PERSIST_DIRECTORY = os.path.join('data', 'chroma_db')
    EMBEDDINGS_COLLECTION_NAME = "event_filter_embeddings"
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')

config = Config()
```

### Step 3.2: Create Request/Response Models

Create `backend/app/models/request_models.py`:

```python
from pydantic import BaseModel, Field
from typing import Optional

class FilterOptions(BaseModel):
    """Options for filter selection."""
    maxFiltersPerCategory: int = Field(default=10, gt=0)
    minConfidence: float = Field(default=0.6, ge=0.0, le=1.0)

class FilterQueryRequest(BaseModel):
    """Request model for filter analysis."""
    query: str = Field(..., min_length=1, max_length=1000)
    options: Optional[FilterOptions] = Field(default_factory=FilterOptions)

class FilterResponse(BaseModel):
    """Response model for filter selection."""
    originalQuery: str
    translatedQuery: str
    detectedLanguage: str
    reducedFilters: dict
    confidence: dict
    reasoning: dict
    processingTime: str
    stages: dict
```

### Step 3.3: Ollama Client Service

Create `backend/app/services/ollama_client.py`:

```python
from typing import List
import requests
from app.config import config
import logging

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self):
        self.base_url = config.OLLAMA_URL
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for given text.
        
        Args:
            text: Input text to embed
        
        Returns:
            Embedding vector as list of floats
        """
        try:
            url = f"{self.base_url}/api/embeddings"
            payload = {
                "model": config.OLLAMA_EMBEDDING_MODEL,
                "prompt": text,
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            embedding = response.json().get("embedding", [])
            if not embedding:
                raise ValueError("Empty embedding returned from Ollama")
            
            return embedding
        
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            raise
    
    def generate_response(self, prompt: str) -> str:
        """
        Generate text response from LLM.
        
        Args:
            prompt: Input prompt for the LLM
        
        Returns:
            Generated response text
        """
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": config.OLLAMA_LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.15,  # Low temperature for consistent results
            }
            
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            return response.json().get("response", "")
        
        except Exception as e:
            logger.error(f"❌ Error generating response: {e}")
            raise
    
    def check_connection(self) -> bool:
        """Check if Ollama service is accessible."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
```

### Step 3.4: Embedding Service

Create `backend/app/services/embedding_service.py`:

```python
import logging
import os
from typing import List, Dict
import numpy as np
from chromadb import PersistentClient
from chromadb.config import Settings

from app.config import config
from app.services.ollama_client import OllamaClient
from app.utils.similarity import cosine_similarity

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for managing embeddings and similarity search."""
    
    def __init__(self):
        """Initialize embedding service."""
        self.ollama_client = OllamaClient()
        self.embeddings_cache = {}
        self.filter_embeddings = []
        self.chroma_client = self._init_chroma()
        self.load_embeddings()
    
    def _init_chroma(self):
        """Initialize ChromaDB client."""
        try:
            client = PersistentClient(
                path=config.PERSIST_DIRECTORY,
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info("✅ Connected to ChromaDB")
            return client
        except Exception as e:
            logger.error(f"❌ ChromaDB initialization error: {e}")
            raise
    
    def load_embeddings(self):
        """Load pre-computed embeddings from ChromaDB."""
        if not os.path.exists(config.PERSIST_DIRECTORY):
            logger.warning(f"⚠️ No embeddings found. Run generate_embeddings.py first")
            return
        
        try:
            collection = self.chroma_client.get_collection(
                name=config.EMBEDDINGS_COLLECTION_NAME
            )
            results = collection.get(include=["metadatas", "embeddings"])
            
            self.filter_embeddings = [
                {
                    "category": meta.get("category", ""),
                    "subcategory": meta.get("subcategory", ""),
                    "name": meta.get("name", ""),
                    "description": meta.get("description", ""),
                    "embedding": embedding
                }
                for meta, embedding in zip(results["metadatas"], results["embeddings"])
            ]
            
            logger.info(f"✅ Loaded {len(self.filter_embeddings)} embeddings")
        
        except Exception as e:
            logger.error(f"❌ Error loading embeddings: {e}")
    
    def is_loaded(self) -> bool:
        """Check if embeddings are loaded."""
        return len(self.filter_embeddings) > 0
    
    def get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for query (with caching)."""
        if query in self.embeddings_cache:
            return self.embeddings_cache[query]
        
        embedding = self.ollama_client.generate_embedding(query)
        self.embeddings_cache[query] = embedding
        return embedding
    
    def clean_query(self, query: str) -> str:
        """
        Clean query text.
        
        - Lowercase
        - Remove special characters
        - Remove stopwords
        """
        import re
        import unicodedata
        
        # Normalize accents
        query = unicodedata.normalize("NFKD", query).encode("ascii", "ignore").decode("utf-8")
        
        # Lowercase and remove special characters
        query = re.sub(r"[^a-z\s]", " ", query.lower())
        
        return query
    
    def find_similar_filters(self, query: str) -> List[Dict]:
        """
        Find most similar filters using embedding similarity.
        
        Args:
            query: User query text
        
        Returns:
            List of top-K similar filters with scores
        """
        if not self.filter_embeddings:
            logger.warning("⚠️ No embeddings loaded!")
            return []
        
        # Clean and embed query
        cleaned_query = self.clean_query(query)
        logger.info(f"🔍 Cleaned query: '{cleaned_query}'")
        
        query_embedding = self.get_query_embedding(cleaned_query)
        
        # Calculate similarities
        results = []
        for filter_data in self.filter_embeddings:
            similarity_score = cosine_similarity(
                query_embedding,
                filter_data['embedding']
            )
            
            results.append({
                'category': filter_data['category'],
                'subcategory': filter_data['subcategory'],
                'name': filter_data['name'],
                'description': filter_data['description'],
                'score': float(similarity_score)
            })
        
        # Sort by score and return top-K
        results = sorted(results, key=lambda x: x['score'], reverse=True)
        return results[:config.TOP_K_SIMILARITY]
```

### Step 3.5: Filter Selector Service (LLM Refinement)

Create `backend/app/services/filter_selector.py`:

```python
import json
import logging
from typing import Dict, List, Any
import re

from app.config import config
from app.services.embedding_service import EmbeddingService
from app.services.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class SmartFilterSelector:
    """Service for intelligent filter selection using embeddings + LLM."""
    
    def __init__(self):
        """Initialize filter selector."""
        self.embedding_service = EmbeddingService()
        self.ollama_client = OllamaClient()
    
    def is_ready(self) -> bool:
        """Check if service is ready."""
        return self.embedding_service.is_loaded()
    
    def select_filters(
        self,
        query: str,
        max_filters: int = None,
        min_confidence: float = None
    ) -> Dict[str, Any]:
        """
        Select filters using hybrid approach (embeddings + LLM).
        
        Stage 1: Embedding-based fast candidate finding
        Stage 2: LLM-based intelligent refinement
        
        Args:
            query: User natural language query
            max_filters: Maximum filters per category
            min_confidence: Minimum confidence threshold
        
        Returns:
            Dictionary with selected filters and confidence scores
        """
        max_filters = max_filters or config.TOP_K_SIMILARITY
        min_confidence = min_confidence or config.MIN_CONFIDENCE_THRESHOLD
        
        logger.info(f"🔍 Processing query: '{query}'")
        
        # Stage 1: Embedding-based search
        logger.info("📊 Stage 1: Embedding-based search...")
        candidates = self.embedding_service.find_similar_filters(query)
        logger.info(f"   ✅ Found {len(candidates)} candidates")
        
        if not candidates:
            return {
                'query': query,
                'reducedFilters': [],
                'confidence': {},
                'reasoning': {'error': 'No embeddings loaded'}
            }
        
        # Stage 2: LLM-based refinement
        logger.info("🤖 Stage 2: LLM-based refinement...")
        refined_result = self._refine_with_llm(query, candidates, max_filters)
        
        return {
            'query': query,
            'candidates': candidates,  # For debugging
            'reducedFilters': refined_result.get('reducedFilters', []),
            'confidence': refined_result.get('confidence', {}),
            'reasoning': refined_result.get('reasoning', {})
        }
    
    def _refine_with_llm(
        self,
        query: str,
        candidates: List[Dict],
        max_per_category: int
    ) -> Dict[str, Any]:
        """
        Refine filter candidates using LLM.
        
        Args:
            query: Original user query
            candidates: Candidate filters from embedding search
            max_per_category: Max filters per category
        
        Returns:
            Refined filters with confidence and reasoning
        """
        try:
            # Format candidates for prompt
            candidates_str = json.dumps(
                [
                    {
                        'name': c['name'],
                        'category': c['category'],
                        'subcategory': c.get('subcategory', ''),
                        'description': c.get('description', ''),
                        'embedding_score': round(c['score'], 3)
                    }
                    for c in candidates
                ],
                indent=2
            )
            
            # Create prompt for LLM
            prompt = self._build_refinement_prompt(query, candidates_str, max_per_category)
            
            # Call LLM
            logger.info("📝 Calling LLM for refinement...")
            response = self.ollama_client.generate_response(prompt)
            
            # Parse LLM response
            result = self._parse_llm_response(response)
            logger.info("   ✅ LLM refinement complete")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ LLM refinement error: {e}")
            return {
                'reducedFilters': [],
                'confidence': {},
                'reasoning': {'error': str(e)}
            }
    
    def _build_refinement_prompt(
        self,
        query: str,
        candidates_str: str,
        max_per_category: int
    ) -> str:
        """
        Build prompt for LLM filter refinement.
        
        Returns:
            Prompt string for LLM
        """
        return f"""You are an expert filter recommendation system for log analysis.

User Query: "{query}"

Available filter candidates (from semantic search):
{candidates_str}

Your task:
1. Analyze the user query and understand what logs they want to see
2. From the candidates provided, select the MOST RELEVANT filters
3. Group filters by category
4. For each category, provide a confidence score (0.0 to 1.0)
5. Explain your reasoning

STRICT RULES:
- Return ONLY valid JSON output, no extra text
- Do NOT invent new filters; use only the exact names from candidates
- If no candidates are relevant, return empty lists
- Keep filters grouped by category

Return JSON in this exact format:
{{
  "reducedFilters": [
    {{"name": "filter_name", "category": "category_name", "subcategory": "sub_name"}},
    ...
  ],
  "confidence": {{
    "category_name": 0.95,
    ...
  }},
  "reasoning": {{
    "category_name": "Why this filter is relevant...",
    ...
  }}
}}

Respond ONLY with the JSON, no markdown or code blocks."""
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured format.
        
        Args:
            response: LLM response text
        
        Returns:
            Parsed result dictionary
        """
        try:
            # Try to extract JSON from response
            # Sometimes LLM wraps it in markdown code blocks
            
            # Remove markdown code blocks if present
            response = re.sub(r'```json\n?', '', response)
            response = re.sub(r'```\n?', '', response)
            response = response.strip()
            
            # Parse JSON
            result = json.loads(response)
            
            return {
                'reducedFilters': result.get('reducedFilters', []),
                'confidence': result.get('confidence', {}),
                'reasoning': result.get('reasoning', {})
            }
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse LLM response: {e}")
            logger.error(f"Response was: {response[:500]}")
            
            return {
                'reducedFilters': [],
                'confidence': {},
                'reasoning': {'error': f'Failed to parse response: {e}'}
            }
```

### Step 3.6: Similarity Utility

Create `backend/app/utils/similarity.py`:

```python
import numpy as np
from typing import List

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec_a: First vector
        vec_b: Second vector
    
    Returns:
        Cosine similarity score (0 to 1)
    """
    try:
        a = np.array(vec_a)
        b = np.array(vec_b)
        
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        similarity = dot_product / (norm_a * norm_b)
        return float(np.clip(similarity, 0.0, 1.0))
    
    except Exception:
        return 0.0
```

### Step 3.7: Flask Application Setup

Create `backend/app/main.py`:

```python
import logging
from flask import Flask
from flask_cors import CORS

from app.config import config
from app.routes.filter_routes import filter_bp

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("rbc-filter-service")

def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app, origins=config.CORS_ORIGINS)
    
    # Register blueprints
    app.register_blueprint(filter_bp)
    
    # Startup logging
    @app.before_request
    def startup():
        if not hasattr(app, 'startup_done'):
            logger.info("🚀 RBC Filter Service Started")
            logger.info(f"📊 Ollama URL: {config.OLLAMA_URL}")
            logger.info(f"🤖 LLM Model: {config.OLLAMA_LLM_MODEL}")
            logger.info(f"📝 Embedding Model: {config.OLLAMA_EMBEDDING_MODEL}")
            app.startup_done = True
    
    return app

app = create_app()
```

### Step 3.8: API Routes

Create `backend/app/routes/filter_routes.py`:

```python
import logging
from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.config import config
from app.models.request_models import FilterQueryRequest
from app.services.filter_selector import SmartFilterSelector
from app.services.ollama_client import OllamaClient

logger = logging.getLogger(__name__)
filter_bp = Blueprint('filter', __name__)

# Initialize services
filter_selector = SmartFilterSelector()
ollama_client = OllamaClient()

@filter_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status including Ollama and embeddings status
    """
    ollama_connected = ollama_client.check_connection()
    embeddings_loaded = filter_selector.is_ready()
    
    status = "healthy" if (ollama_connected and embeddings_loaded) else "unhealthy"
    
    return jsonify({
        'status': status,
        'ollama_connected': ollama_connected,
        'embeddings_loaded': embeddings_loaded,
        'message': 'Service is ' + ('ready' if status == 'healthy' else 'not ready')
    }), (200 if status == 'healthy' else 503)

@filter_bp.route('/api/filters/analyze-query', methods=['POST'])
def analyze_query():
    """
    Analyze natural language query and return recommended filters.
    
    Request JSON:
    {
      "query": "Show authentication errors from last hour",
      "options": {
        "maxFiltersPerCategory": 10,
        "minConfidence": 0.6
      }
    }
    
    Response JSON:
    {
      "query": "...",
      "reducedFilters": [...],
      "confidence": {...},
      "reasoning": {...}
    }
    """
    try:
        # Parse request
        data = request.get_json()
        logger.info(f"🔍 Query request: {data}")
        
        # Validate with Pydantic
        try:
            query_request = FilterQueryRequest(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Invalid request',
                'details': e.errors()
            }), 422
        
        # Check if service is ready
        if not filter_selector.is_ready():
            return jsonify({
                'error': 'Service not ready',
                'message': 'Embeddings not loaded. Run generate_embeddings.py first'
            }), 503
        
        # Process query
        result = filter_selector.select_filters(
            query=query_request.query,
            max_filters=query_request.options.maxFiltersPerCategory,
            min_confidence=query_request.options.minConfidence
        )
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@filter_bp.route('/api/filters/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint."""
    return jsonify({
        'message': 'Filter service is running!',
        'service_ready': filter_selector.is_ready()
    }), 200
```

### Step 3.9: Embedding Generation Script

Create `backend/scripts/generate_embeddings.py`:

```python
import logging
import os
import sys
import uuid
from pathlib import Path

import chromadb
from chromadb.config import Settings
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import config
from app.services.ollama_client import OllamaClient
from app.utils.filter_loader import FilterLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("generate_embeddings")

def generate_embeddings():
    """Generate and store embeddings for all filters in ChromaDB."""
    
    logger.info("🔄 Generating Embeddings for RBC Log Analyzer Filters")
    
    # Initialize services
    try:
        filter_loader = FilterLoader(config.FILTER_CONFIG_PATH)
        ollama_client = OllamaClient()
    except Exception as e:
        logger.error(f"❌ Initialization error: {e}")
        return
    
    # Check Ollama connection
    logger.info("1️⃣ Checking Ollama connection...")
    if not ollama_client.check_connection():
        logger.error(f"❌ Cannot connect to Ollama at {config.OLLAMA_URL}")
        logger.error("   Make sure Ollama is running: ollama serve")
        return
    logger.info(f"✅ Connected to Ollama")
    
    # Load filter data
    logger.info("2️⃣ Loading filter configuration...")
    try:
        flattened_filters = filter_loader.flatten_filter_values()
        logger.info(f"✅ Loaded {len(flattened_filters)} filter values")
    except Exception as e:
        logger.error(f"❌ Error loading filters: {e}")
        return
    
    # Initialize ChromaDB
    logger.info("3️⃣ Initializing ChromaDB...")
    try:
        os.makedirs(config.PERSIST_DIRECTORY, exist_ok=True)
        
        client = chromadb.PersistentClient(
            path=config.PERSIST_DIRECTORY,
            settings=Settings(anonymized_telemetry=False)
        )
        collection = client.get_or_create_collection(
            name=config.EMBEDDINGS_COLLECTION_NAME
        )
        logger.info("✅ ChromaDB initialized")
    except Exception as e:
        logger.error(f"❌ ChromaDB initialization error: {e}")
        return
    
    # Generate embeddings
    logger.info(f"4️⃣ Generating embeddings using {config.OLLAMA_EMBEDDING_MODEL}...")
    
    success_count = 0
    error_count = 0
    
    for filter_value in tqdm(flattened_filters, desc="Generating"):
        name = filter_value.get('name', '')
        description = filter_value.get('description', '')
        category = filter_value.get('category', '')
        subcategory = filter_value.get('subcategory', '')
        
        try:
            # Create text to embed (include all context)
            text_to_embed = (
                f"Item: {name}\n"
                f"Category: {category}\n"
                f"Subcategory: {subcategory}\n"
                f"Description: {description}"
            )
            
            # Generate embedding
            embedding = ollama_client.generate_embedding(text_to_embed)
            
            # Create metadata
            metadata = {
                "name": str(name),
                "category": str(category),
                "subcategory": str(subcategory),
                "description": str(description)
            }
            
            # Store in ChromaDB
            collection.add(
                ids=[str(uuid.uuid4())],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[description]
            )
            
            success_count += 1
        
        except Exception as e:
            logger.warning(f"⚠️ Error for '{name}': {e}")
            error_count += 1
            continue
    
    # Summary
    logger.info("✅ Embedding generation complete!")
    logger.info(f"   Success: {success_count}")
    logger.info(f"   Errors: {error_count}")
    logger.info(f"   Database: {config.PERSIST_DIRECTORY}")
    logger.info("🚀 Ready to use smart filters!")

if __name__ == '__main__':
    generate_embeddings()
```

### Step 3.10: Entry Point

Create `backend/run.py`:

```python
from app.config import config
from app.main import app

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )
```

### Step 3.11: Create .env File

Create `backend/.env`:

```env
OLLAMA_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large
OLLAMA_LLM_MODEL=mistral
FLASK_PORT=5000
FLASK_DEBUG=True
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## Phase 4: Frontend Integration

### Step 4.1: Create TypeScript API Client

Create a file in your React/TypeScript frontend (e.g., `frontend/src/services/filterApi.ts`):

```typescript
interface FilterOptions {
  maxFiltersPerCategory?: number;
  minConfidence?: number;
}

interface AnalyzeQueryRequest {
  query: string;
  options?: FilterOptions;
}

interface FilterResult {
  query: string;
  reducedFilters: Array<{
    name: string;
    category: string;
    subcategory: string;
  }>;
  confidence: Record<string, number>;
  reasoning: Record<string, string>;
  candidates?: any[];
}

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';

export async function analyzeQuery(request: AnalyzeQueryRequest): Promise<FilterResult> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/filters/analyze-query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error analyzing query:', error);
    throw error;
  }
}

export async function checkHealth(): Promise<{
  status: string;
  ollama_connected: boolean;
  embeddings_loaded: boolean;
}> {
  try {
    const response = await fetch(`${BACKEND_URL}/health`);
    return await response.json();
  } catch (error) {
    console.error('Error checking health:', error);
    throw error;
  }
}
```

### Step 4.2: Create React Component

Create `frontend/src/components/SmartFilterInput.tsx`:

```typescript
import React, { useState } from 'react';
import { analyzeQuery, checkHealth } from '../services/filterApi';

interface Props {
  onFiltersSelected: (filters: string[]) => void;
  onLoading?: (loading: boolean) => void;
}

export const SmartFilterInput: React.FC<Props> = ({ onFiltersSelected, onLoading }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedFilters, setSelectedFilters] = useState<string[]>([]);
  const [reasoning, setReasoning] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim()) {
      return;
    }

    setLoading(true);
    onLoading?.(true);
    setError(null);

    try {
      // Check service health first
      const health = await checkHealth();
      if (health.status !== 'healthy') {
        setError('Backend service is not ready. Please check Ollama is running.');
        return;
      }

      // Analyze query
      const result = await analyzeQuery({
        query: query,
        options: {
          maxFiltersPerCategory: 10,
          minConfidence: 0.6,
        },
      });

      // Extract filter names
      const filterNames = result.reducedFilters.map(f => f.name);
      setSelectedFilters(filterNames);
      setReasoning(result.reasoning);
      onFiltersSelected(filterNames);

    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to analyze query: ${message}`);
    } finally {
      setLoading(false);
      onLoading?.(false);
    }
  };

  return (
    <div className="smart-filter-container">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="e.g., 'Show authentication errors from the last hour'"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading}
          className="filter-input"
        />
        <button type="submit" disabled={loading || !query.trim()}>
          {loading ? 'Analyzing...' : 'Analyze with AI'}
        </button>
      </form>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {selectedFilters.length > 0 && (
        <div className="results">
          <h3>Recommended Filters</h3>
          <div className="filter-tags">
            {selectedFilters.map(filter => (
              <div key={filter} className="filter-tag">
                <span>{filter}</span>
              </div>
            ))}
          </div>

          {Object.keys(reasoning).length > 0 && (
            <div className="reasoning">
              <h4>Why These Filters?</h4>
              {Object.entries(reasoning).map(([category, reason]) => (
                <p key={category}>
                  <strong>{category}:</strong> {reason}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
```

### Step 4.3: CSS Styling

Create `frontend/src/components/SmartFilterInput.css`:

```css
.smart-filter-container {
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-bottom: 20px;
  background-color: #f9f9f9;
}

.smart-filter-container form {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.filter-input {
  flex: 1;
  padding: 10px 15px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
}

.filter-input:focus {
  outline: none;
  border-color: #4CAF50;
  box-shadow: 0 0 5px rgba(76, 175, 80, 0.3);
}

.smart-filter-container button {
  padding: 10px 20px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
  transition: background-color 0.3s;
}

.smart-filter-container button:hover:not(:disabled) {
  background-color: #45a049;
}

.smart-filter-container button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.error-message {
  padding: 12px;
  margin-bottom: 15px;
  background-color: #ffebee;
  border-left: 4px solid #f44336;
  color: #c62828;
  border-radius: 4px;
}

.results {
  margin-top: 20px;
}

.results h3 {
  margin-top: 0;
  color: #333;
}

.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 15px;
}

.filter-tag {
  display: inline-block;
  padding: 8px 12px;
  background-color: #e8f5e9;
  border: 1px solid #4CAF50;
  border-radius: 20px;
  color: #2e7d32;
  font-size: 13px;
  font-weight: 500;
}

.reasoning {
  background-color: #e3f2fd;
  padding: 15px;
  border-radius: 4px;
  margin-top: 15px;
}

.reasoning h4 {
  margin-top: 0;
  color: #1565c0;
}

.reasoning p {
  margin: 8px 0;
  font-size: 13px;
  color: #0d47a1;
}
```

---

## Phase 5: Testing & Optimization

### Step 5.1: Start the Backend

```bash
# Terminal 1: Start Ollama (if not running as service)
ollama serve

# Terminal 2: Navigate to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Generate embeddings (one-time setup)
python scripts/generate_embeddings.py

# Start Flask server
python run.py
```

You should see:
```
* Running on http://0.0.0.0:5000
🚀 RBC Filter Service Started
✅ Loaded 50 embeddings
```

### Step 5.2: Test API Endpoints

Use curl or Postman to test:

```bash
# Test health check
curl http://localhost:5000/health

# Test filter analysis
curl -X POST http://localhost:5000/api/filters/analyze-query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show authentication errors from the last hour",
    "options": {
      "maxFiltersPerCategory": 10,
      "minConfidence": 0.6
    }
  }'
```

### Step 5.3: Common Issues & Solutions

**Issue 1: "Cannot connect to Ollama"**
```
Solution:
1. Make sure Ollama is running: ollama serve
2. Check OLLAMA_URL in .env is correct
3. Test: curl http://localhost:11434/api/tags
```

**Issue 2: "No embeddings loaded"**
```
Solution:
1. Run: python scripts/generate_embeddings.py
2. Check data/filters_config.json exists and has filters
3. Wait for embeddings to finish generating
```

**Issue 3: "LLM response parsing error"**
```
Solution:
1. Check Ollama has the model: ollama list
2. Try: ollama pull mistral
3. Check logs for full error message
4. Verify prompt format in filter_selector.py
```

**Issue 4: "CORS errors in frontend"**
```
Solution:
1. Update CORS_ORIGINS in .env
2. Make sure backend Flask is running
3. Check frontend makes requests to correct URL
```

### Step 5.4: Performance Optimization

**Cache Query Embeddings:**
The embedding service already caches embeddings, so repeated queries are instant.

**Batch Processing:**
For processing multiple queries, you can batch them:

```python
# Add to embedding_service.py
def find_similar_filters_batch(self, queries: List[str]) -> List[List[Dict]]:
    """Process multiple queries efficiently."""
    return [self.find_similar_filters(q) for q in queries]
```

**Reduce Candidates:**
If slow, reduce TOP_K_SIMILARITY in config.py:
```python
TOP_K_SIMILARITY = 10  # Instead of 20
```

### Step 5.5: Monitoring & Logging

Check logs for performance:

```bash
# Tail logs in real-time
tail -f app.log  # Linux/Mac

# Or use Python logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Summary Checklist

✅ **Phase 1: Setup**
- [ ] Installed Ollama and pulled models
- [ ] Created backend directory structure
- [ ] Created Python virtual environment
- [ ] Installed dependencies

✅ **Phase 2: Data**
- [ ] Listed all filters from your events page
- [ ] Created filters_config.json
- [ ] Created FilterLoader utility

✅ **Phase 3: Backend**
- [ ] Created Config class
- [ ] Created Request/Response models
- [ ] Created OllamaClient service
- [ ] Created EmbeddingService
- [ ] Created SmartFilterSelector service
- [ ] Created API routes
- [ ] Created embedding generation script
- [ ] Set up Flask app
- [ ] Created .env file

✅ **Phase 4: Frontend**
- [ ] Created TypeScript API client
- [ ] Created React component
- [ ] Added CSS styling
- [ ] Integrated with events page

✅ **Phase 5: Testing**
- [ ] Generated embeddings
- [ ] Started backend server
- [ ] Tested API endpoints
- [ ] Fixed any issues
- [ ] Tested frontend integration

---

## Next Steps

1. **Customize for Your Domain:**
   - Update prompt templates in filter_selector.py for your log domain
   - Add more sophisticated filter categories as needed

2. **Add More Features:**
   - Save user preferences
   - Track popular filter combinations
   - Add A/B testing for different prompt templates

3. **Performance Improvements:**
   - Add caching layer (Redis)
   - Optimize embedding generation
   - Add query result caching

4. **Production Deployment:**
   - Use production-grade WSGI server (Gunicorn)
   - Add request rate limiting
   - Set up proper error monitoring
   - Deploy to cloud (AWS, GCP, etc.)

---

## Additional Resources

- **Embeddings Deep Dive:** See `ARCHITECTURE_AND_CONCEPTS.md` in the smart-filter-selector repo
- **LangChain Docs:** https://python.langchain.com
- **ChromaDB:** https://docs.trychroma.com
- **Ollama Models:** https://ollama.ai/library


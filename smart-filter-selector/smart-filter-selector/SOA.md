# Intelligent Filter Selection System

**Repository**: [smart-filter-selector](https://github.com/ikos-lab/smart-filter-selector)

**Standalone Python microservice** for AI-powered filter recommendation that analyzes natural language queries and returns optimized subsets of filtering options.

## 🎯 Problem Statement

Knowledge Management Systems often contain extensive filtering options across multiple categories:
- **100+ technical tools** (MATLAB, SCADE, Python, etc.)
- **50+ specializations** across various domains (Railway, Energy, etc.)
- **Complex hierarchical relationships** between filters

**Challenge:** Users are overwhelmed by too many filter choices, making it difficult to find relevant results efficiently.

**Solution:** A standalone Python-based AI microservice that:
- Accepts filter configurations via API or JSON files
- Analyzes user queries (e.g., "railway signaling expert with ERTMS")
- Returns only the 5-15 most relevant filter values per category
- Reduces options by 70-90%
- Can be integrated with any frontend application

## 🏢 Architecture: Standalone Microservice

This is a **completely independent Python service** that:
- ✅ Runs separately from any main application
- ✅ Built with Python 3.11+ and FastAPI
- ✅ Has its own database and cache
- ✅ Exposes REST API endpoints
- ✅ Dockerized for easy deployment
- ✅ Uses Ollama for local LLM/embedding inference (no external API keys needed)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  Client Application                     │
│                        (KMS)                            │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST API
                     ▼
┌─────────────────────────────────────────────────────────┐
│         AI Filter Selection Microservice                │
│                  (Port 8000)                            │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────┐   │
│  │          FastAPI REST API Layer                  │   │
│  │   - /api/filter/analyze-query                    │   │
│  │   - /api/filter/feedback                         │   │
│  │   - /api/filter/upload-config                    │   │
│  └────────────┬─────────────────────────────────────┘   │
│               ▼                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │       Query Analysis Service                     │   │
│  │   - NLP tokenization                             │   │
│  │   - Keyword extraction                           │   │
│  │   - Intent recognition                           │   │
│  └────────────┬─────────────────────────────────────┘   │
│               ▼                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │     Embedding Service (Ollama)                   │   │
│  │   - Convert query to embeddings                  │   │
│  │   - Convert filter values to vectors             │   │
│  └────────────┬─────────────────────────────────────┘   │
│               ▼                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │      Similarity Matching Engine                  │   │
│  │   - Cosine similarity computation                │   │
│  │   - Hierarchical filter resolution               │   │
│  │   - Confidence scoring                           │   │
│  └────────────┬─────────────────────────────────────┘   │
│               ▼                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │       Filter Subset Generator                    │   │
│  │   - Top-K selection per category                 │   │
│  │   - Maintain hierarchy relationships             │   │
│  │   - Apply domain-specific rules                  │   │
│  └──────────────────────────────────────────────────┘   │
└────────┬────────────────────┬────────────────────┬──────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌────────────────┐   ┌────────────────┐   ┌──────────────┐
│   MongoDB      │   │   Redis Cache  │   │   Ollama     │
│ (Embeddings &  │   │  (Query Cache) │   │  (LLM/Embed) │
│  Feedback)     │   │                │   │ (Port 11434) │
└────────────────┘   └────────────────┘   └──────────────┘
```

### Service Communication:
- **External API**: RESTful endpoints for any client application
- **Ollama**: Local LLM inference (no external API keys needed)
- **MongoDB**: Stores pre-computed embeddings and user feedback
- **Redis**: Caches frequent queries for fast response

---

## 🛠️ Technical Approaches

### **Approach 1: Embedding-Based Similarity (Recommended)**

**How it works:**
1. **Pre-compute embeddings** for all filter values using Ollama
2. Generate **query embedding** when user submits a search
3. Calculate **cosine similarity** between query and each filter value
4. Return **top-K most similar** values per category with confidence scores

**Advantages:**
- Handles synonyms and semantic relationships
- Fast inference (pre-computed embeddings)
- No training data required initially
- Can be improved with fine-tuning

**Ollama Models to Use:**
- `nomic-embed-text` - Best for embeddings (768 dimensions)
- `all-minilm` - Lightweight alternative (384 dimensions)

**Implementation:**
```python
import requests
import numpy as np

# Generate embeddings using Ollama
def generate_embedding(text):
    response = requests.post('http://ollama:11434/api/embeddings', 
        json={
            'model': 'nomic-embed-text',
            'prompt': text
        }
    )
    return response.json()['embedding']

# Compare with pre-computed filter embeddings
query_embedding = generate_embedding('railway ERTMS expert')
similarities = [
    cosine_similarity(query_embedding, filter_data['embedding'])
    for filter_data in filter_embeddings
]
```

---

### **Approach 2: LLM-Based Filter Selection**

**How it works:**
1. Send user query + formOption.js structure to **Ollama LLM**
2. Ask LLM to select relevant filters with reasoning
3. Parse structured JSON response

**Advantages:**
- Best understanding of context and nuance
- Can handle complex hierarchical relationships
- Provides natural language explanations

**Ollama Models to Use:**
- `llama3.2` (3B) - Fast and efficient
- `mistral` (7B) - Better reasoning
- `llama3.1` (8B) - Balanced performance

**Prompt Template:**
```python
  def build_prompt(user_query, form_options):
      prompt = f"""
              Given this user query: "{user_query}"
              
              And these available filter categories from formOption.js:
              - tool: {form_options['tool'][:10]}... (100+ total)
              - environnement-domain: {form_options['environnement-domain']}
              - domain-speciality: {{...}}
              
              Return a JSON object with ONLY the most relevant 5-10 filter values per category.
              Include confidence scores (0-1) and reasoning.
              
              Response format:
              {{
                "reducedFilters": {{
                  "tool": ["SCADE", "EN50128"],
                  "environnement-domain": ["Railway"]
                }},
                "confidence": {{"tool": 0.87, "environnement-domain": 0.95}},
                "reasoning": "Query mentions railway and ERTMS which requires SCADE tool"
              }}
      """
    return prompt
```

---

### **Approach 3: Hybrid (Embeddings + LLM)**

**How it works:**
1. Use **embeddings** for initial filtering (top 30-50 candidates)
2. Use **LLM** to refine selection and explain reasoning
3. Best of both worlds: speed + intelligence

---

### **Approach 4: Rule-Based + Keyword Matching**

**How it works:**
1. Extract keywords from query (NLP tokenization)
2. Match against filter values using fuzzy matching
3. Apply domain-specific rules (e.g., "metro" → Railway → CBTC)

**Advantages:**
- No external dependencies
- Fast and deterministic
- Good for MVP/prototype

**Implementation:**
```python
import re
from typing import List, Dict
from difflib import SequenceMatcher

def extract_keywords(query: str) -> List[str]:
    """Extract keywords from query using NLP tokenization"""
    # Remove common words, lowercase, tokenize
    query = query.lower()
    keywords = re.findall(r'\b\w+\b', query)
    stopwords = {'the', 'a', 'an', 'with', 'for', 'expert', 'engineer'}
    return [kw for kw in keywords if kw not in stopwords]

def fuzzy_match_score(keyword: str, filter_value: str) -> float:
    """Calculate fuzzy matching score"""
    return SequenceMatcher(None, keyword.lower(), filter_value.lower()).ratio()

def filter_by_keywords(query: str, form_options: Dict) -> Dict:
    """Match filters using keyword extraction"""
    keywords = extract_keywords(query)  # ["railway", "ERTMS", "SCADE"]
    matches = {}
    
    # Direct keyword matching with fuzzy search
    for tool in form_options['tool']:
        scores = [fuzzy_match_score(kw, tool) for kw in keywords]
        max_score = max(scores) if scores else 0
        if max_score > 0.6:  # Threshold
            matches[tool] = max_score
    
    # Hierarchical resolution
    if any('railway' in kw for kw in keywords):
        matches['environnement-domain'] = ['Railway']
        # Trigger Railway-specific filters
    
    return matches
```

---

## 🐳 Deployment Architecture (Docker + Ollama)

### **Docker Compose Structure (Standalone Service)**

```yaml
version: '3.8'

services:
  # Ollama service for embeddings and LLM inference
  ollama:
    image: ollama/ollama:latest
    container_name: smart-filter-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]  # Optional: for GPU acceleration

  # Python FastAPI service for AI filter recommendation
  ai-filter-service:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: smart-filter-service
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_URL=http://ollama:11434
      - MONGODB_URL=mongodb://mongodb:27017/smart_filter
      - REDIS_URL=redis://redis:6379
      - FILTER_CONFIG_PATH=/app/data/filter_config.json
    depends_on:
      - ollama
      - mongodb
      - redis
    volumes:
      - ./app:/app/app
      - ./data:/app/data
      - ./scripts:/app/scripts
    restart: unless-stopped
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # MongoDB for storing embeddings and feedback
  mongodb:
    image: mongo:latest
    container_name: smart-filter-mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      - MONGO_INITDB_DATABASE=smart_filter
    restart: unless-stopped

  # Redis for caching query results
  redis:
    image: redis:alpine
    container_name: smart-filter-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped

volumes:
  ollama_data:
    driver: local
  mongodb_data:
    driver: local
  redis_data:
    driver: local
```

### **Integration with Existing Applications**

If you want to integrate this with an existing application (like KMS):

```yaml
# In your existing docker-compose.yml, add:
services:
  # ... your existing services ...
  
  # Add the AI Filter Service
  ai-filter-service:
    image: smart-filter-selector:latest
    container_name: smart-filter-service
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_URL=http://ollama:11434
    networks:
      - your-app-network
  
  # Your backend can now call: http://smart-filter-service:8000/api/filter/analyze-query
```

---

## 📁 Project Structure

```
smart-filter-selector/                # Root directory
├── app/
│   ├── __init__.py
│   ├── main.py                       # FastAPI application entry point
│   ├── config.py                     # Configuration (Ollama URL, MongoDB, etc.)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request_models.py         # Pydantic request models
│   │   └── response_models.py        # Pydantic response models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ollama_client.py          # Ollama API client
│   │   ├── query_analyzer.py         # NLP query analysis
│   │   ├── embedding_service.py      # Embedding generation & matching
│   │   ├── llm_service.py            # LLM-based filter selection
│   │   ├── filter_matcher.py         # Rule-based matching
│   │   ├── hybrid_selector.py        # Hybrid approach
│   │   └── feedback_service.py       # User feedback collection
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── similarity.py             # Cosine similarity functions
│   │   ├── filter_loader.py          # Load filter configurations
│   │   └── cache.py                  # Redis caching
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── filter_routes.py          # Filter API endpoints
│   │   ├── config_routes.py          # Configuration management endpoints
│   │   └── health_routes.py          # Health check endpoints
│   └── database/
│       ├── __init__.py
│       ├── mongodb.py                # MongoDB connection
│       └── redis_client.py           # Redis connection
├── data/
│   ├── filter_config.json            # Default filter configuration
│   └── examples/
│       ├── kms_filters.json          # Example: KMS filter config
│       ├── ecommerce_filters.json    # Example: E-commerce filters
│       └── hr_filters.json           # Example: HR system filters
├── tests/
│   ├── __init__.py
│   ├── test_query_analyzer.py
│   ├── test_embedding_service.py
│   ├── test_filter_routes.py
│   └── fixtures/
│       └── test_queries.py
├── scripts/
│   ├── generate_embeddings.py        # Pre-compute embeddings
│   ├── benchmark.py                  # Performance testing
│   └── import_filters.py             # Import filter configs
├── docs/
│   ├── API.md                        # API documentation
│   ├── INTEGRATION.md                # Integration guide
│   └── DEPLOYMENT.md                 # Deployment guide
├── docker-compose.yml                # Docker composition
├── Dockerfile                        # Docker image definition
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variables template
├── .gitignore
└── README.md                         # This file
```

---

## 📦 Installation & Setup

### **Prerequisites**
- Docker & Docker Compose
- 8GB+ RAM (16GB recommended for LLM)
- Optional: NVIDIA GPU for faster inference

### **Quick Start**

```bash
# 1. Clone the repository
git clone https://github.com/ikos-lab/smart-filter-selector.git
cd smart-filter-selector

# 2. Copy environment variables
cp .env.example .env

# 3. Start all services with Docker Compose
docker-compose up -d

# 4. Wait for services to be ready
docker-compose logs -f smart-filter-service
```

### **1. Pull Ollama Models**

```bash
# Pull embedding model
docker exec -it smart-filter-ollama ollama pull nomic-embed-text

# Pull LLM model (choose one based on your resources)
docker exec -it smart-filter-ollama ollama pull llama3.2:3b     # Lightweight (3GB)
docker exec -it smart-filter-ollama ollama pull mistral:7b      # Better quality (7GB)
docker exec -it smart-filter-ollama ollama pull llama3.1:8b     # Best balance (8GB)

# Verify models are installed
docker exec -it smart-filter-ollama ollama list
```

### **2. Upload Your Filter Configuration**

```bash
# Option 1: Use the API to upload filter config
curl -X POST http://localhost:8000/api/config/upload \
  -H "Content-Type: application/json" \
  -d @data/filter_config.json

# Option 2: Place your filter JSON in data/ directory and restart
cp your_filters.json data/filter_config.json
docker-compose restart smart-filter-service
```

### **3. Generate Pre-computed Embeddings**

```bash
# Run the embedding generation script
docker exec -it smart-filter-service python scripts/generate_embeddings.py

# This will:
# 1. Load filter configuration from data/filter_config.json
# 2. Generate embeddings for all filter values using Ollama
# 3. Store in MongoDB for fast lookup
# 4. Create vector indexes for similarity search

# Monitor progress
docker-compose logs -f smart-filter-service
```

### **4. Verify Service is Running**

```bash
# Health check
curl http://localhost:8000/health

# Test query
curl -X POST http://localhost:8000/api/filter/analyze-query \
  -H "Content-Type: application/json" \
  -d '{"query": "railway signaling expert with ERTMS"}'
```

### **5. Access Services**

- **AI Filter API**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **API Documentation (ReDoc)**: http://localhost:8000/redoc
- **Ollama API**: http://localhost:11434
- **MongoDB**: localhost:27017
- **Redis**: localhost:6379

---

## 🔌 Integration with Your Application

### **Example: Integrate with Node.js/Express Backend**

The smart-filter-selector is a Python service, but it can be easily consumed by any Node.js application via HTTP:

```javascript
// In your Node.js backend (e.g., Express)
const axios = require('axios');

const AI_FILTER_SERVICE_URL = process.env.AI_FILTER_URL || 'http://localhost:8000';

async function getSmartFilters(userQuery) {
  try {
    const response = await axios.post(
      `${AI_FILTER_SERVICE_URL}/api/filter/analyze-query`,
      {
        query: userQuery,
        options: {
          maxFiltersPerCategory: 10,
          minConfidence: 0.6
        }
      }
    );
    return response.data;
  } catch (error) {
    console.error('AI Filter Service error:', error);
    // Fallback to showing all filters
    return null;
  }
}

// In your route handler
app.get('/api/consultants/search', async (req, res) => {
  const { query } = req.query;
  
  // Get smart filter recommendations from Python service
  const smartFilters = await getSmartFilters(query);
  
  // Use the reduced filters in your UI
  res.json({
    query,
    suggestedFilters: smartFilters?.reducedFilters,
    confidence: smartFilters?.confidence
  });
});
```

### **Example: Integrate with React Frontend**

```javascript
// React component for smart filter selection
// Calls the Python FastAPI service directly
import React, { useState } from 'react';
import axios from 'axios';

function SmartFilterSelector() {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState(null);
  const [loading, setLoading] = useState(false);

  const analyzeQuery = async () => {
    setLoading(true);
    try {
      // Call the Python FastAPI service
      const response = await axios.post(
        'http://localhost:8000/api/filter/analyze-query',
        { query }
      );
      setFilters(response.data.reducedFilters);
    } catch (error) {
      console.error('Error:', error);
    }
    setLoading(false);
  };

  return (
    <div>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Describe what you're looking for..."
      />
      <button onClick={analyzeQuery} disabled={loading}>
        {loading ? 'Analyzing...' : 'Find Filters'}
      </button>
      
      {filters && (
        <div>
          {/* Render reduced filter options */}
          {Object.entries(filters).map(([category, values]) => (
            <div key={category}>
              <h3>{category}</h3>
              {Array.isArray(values) ? (
                <ul>
                  {values.map(v => <li key={v}>{v}</li>)}
                </ul>
              ) : (
                <pre>{JSON.stringify(values, null, 2)}</pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## 🔧 Implementation Plan

### **Phase 1: MVP (Week 1-2)**

**Goal:** Basic rule-based filter recommendation

1. Create `app/services/query_analyzer.py`
   ```python
   from typing import List
   import re
   
   class QueryAnalyzer:
       def extract_keywords(self, query: str) -> List[str]:
           """Extract meaningful keywords from query"""
           query = query.lower()
           keywords = re.findall(r'\b\w+\b', query)
           stopwords = {'the', 'a', 'an', 'with', 'for', 'in', 'on'}
           return [kw for kw in keywords if kw not in stopwords]
   ```
   
2. Create `app/services/filter_matcher.py`
   ```python
   from difflib import SequenceMatcher
   from typing import Dict, List
   
   class FilterMatcher:
       def fuzzy_match(self, keywords: List[str], 
                      form_options: Dict) -> Dict:
           """Match keywords to filter values"""
           matches = {}
           for category, values in form_options.items():
               matches[category] = self._match_category(keywords, values)
           return matches
   ```
   
3. Add API endpoint in `app/routes/filter_routes.py`:
   ```python
   from fastapi import APIRouter, HTTPException
   from app.models.request_models import FilterQueryRequest
   from app.models.response_models import FilterResponse
   
   router = APIRouter()
   
   @router.post("/api/filter/analyze-query", response_model=FilterResponse)
   async def analyze_query(request: FilterQueryRequest):
       """Analyze query and return reduced filter subset"""
       # Implementation
       pass
   ```

4. Create React component: `<SmartFilterSelector />`
   - Query input field
   - Display reduced filter options
   - Show/hide logic for irrelevant filters

**Test with:**
- "railway ERTMS expert"
- "nuclear instrumentation engineer"
- "metro automation CBTC"

---

### **Phase 2: Embedding-Based (Week 3-4)**

**Goal:** Semantic similarity using Ollama embeddings

1. Integrate Ollama client
   ```python
   # app/services/ollama_client.py
   import requests
   from typing import List
   
   class OllamaClient:
       def __init__(self, base_url: str = "http://ollama:11434"):
           self.base_url = base_url
       
       def generate_embedding(self, text: str, 
                            model: str = "nomic-embed-text") -> List[float]:
           """Generate embedding vector for text"""
           response = requests.post(
               f"{self.base_url}/api/embeddings",
               json={"model": model, "prompt": text}
           )
           response.raise_for_status()
           return response.json()["embedding"]
   ```

2. Pre-compute embeddings for all formOption values
   ```python
   # scripts/generate_embeddings.py
   import json
   from pymongo import MongoClient
   from app.services.ollama_client import OllamaClient
   
   def generate_all_embeddings():
       """Generate and store embeddings for all filter values"""
       client = MongoClient("mongodb://mongodb:27017/")
       db = client.smart_filter
       ollama = OllamaClient()
       
       # Load formOption.js
       with open('data/formOption.js', 'r') as f:
           form_options = json.loads(f.read())
       
       # Generate embeddings
       for category, values in form_options.items():
           for value in values:
               embedding = ollama.generate_embedding(value)
               db.filter_embeddings.insert_one({
                   "category": category,
                   "value": value,
                   "embedding": embedding
               })
   ```

3. Implement cosine similarity search
   ```python
   # app/utils/similarity.py
   import numpy as np
   from typing import List
   
   def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
       """Calculate cosine similarity between two vectors"""
       a = np.array(vec_a)
       b = np.array(vec_b)
       return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
   ```

4. Update API to use embeddings
   ```python
   # app/services/embedding_service.py
   from typing import Dict, List
   from app.services.ollama_client import OllamaClient
   from app.utils.similarity import cosine_similarity
   from pymongo import MongoClient
   
   class EmbeddingService:
       def find_similar_filters(self, query: str, 
                               top_k: int = 10) -> Dict:
           """Find most similar filters using embeddings"""
           query_embedding = self.ollama.generate_embedding(query)
           
           # Retrieve all filter embeddings from MongoDB
           embeddings = self.db.filter_embeddings.find()
           
           # Calculate similarities
           results = []
           for doc in embeddings:
               similarity = cosine_similarity(
                   query_embedding, 
                   doc['embedding']
               )
               results.append({
                   'category': doc['category'],
                   'value': doc['value'],
                   'score': similarity
               })
           
           # Return top-K per category
           return self._group_by_category(results, top_k)
   ```

---

### **Phase 3: LLM Enhancement (Week 5-6)**

**Goal:** Add intelligent reasoning and explanations

1. Create LLM-based filter selector
   ```python
   # app/services/llm_service.py
   import requests
   import json
   from typing import Dict
   
   class LLMFilterSelector:
       def __init__(self, ollama_url: str = "http://ollama:11434"):
           self.ollama_url = ollama_url
       
       def select_filters(self, query: str, 
                         form_options: Dict) -> Dict:
           """Use LLM to select relevant filters"""
           prompt = self._build_prompt(query, form_options)
           
           response = requests.post(
               f"{self.ollama_url}/api/generate",
               json={
                   "model": "llama3.2",
                   "prompt": prompt,
                   "stream": False,
                   "format": "json"
               }
           )
           
           result = response.json()
           return json.loads(result["response"])
       
       def _build_prompt(self, query: str, form_options: Dict) -> str:
           """Build structured prompt for LLM"""
           return f"""You are an expert filter recommendation system.
           
Query: "{query}"

Available filters (sample):
{json.dumps(form_options, indent=2)[:1000]}...

Select the 5-10 most relevant filter values per category.
Return JSON with reducedFilters, confidence scores, and reasoning.
"""
   ```

2. Implement hybrid approach
   ```python
   # app/services/hybrid_selector.py
   from app.services.embedding_service import EmbeddingService
   from app.services.llm_service import LLMFilterSelector
   
   class HybridFilterSelector:
       def __init__(self):
           self.embedding_service = EmbeddingService()
           self.llm_service = LLMFilterSelector()
       
       def select_filters(self, query: str) -> Dict:
           """Use embeddings for initial filtering, LLM for refinement"""
           # Step 1: Fast embedding-based filtering (top 30-50)
           candidates = self.embedding_service.find_similar_filters(
               query, top_k=30
           )
           
           # Step 2: LLM refinement and explanation
           final_selection = self.llm_service.select_filters(
               query, candidates
           )
           
           return final_selection
   ```

3. Add learning mechanism
   ```python
   # app/services/feedback_service.py
   from pymongo import MongoClient
   from datetime import datetime
   
   class FeedbackService:
       def store_feedback(self, query: str, recommended: Dict, 
                         selected: Dict, helpful: bool):
           """Store user feedback for model improvement"""
           self.db.feedback.insert_one({
               "query": query,
               "recommended_filters": recommended,
               "user_selected_filters": selected,
               "was_helpful": helpful,
               "timestamp": datetime.utcnow()
           })
   ```

---

### **Phase 4: Optimization & Production (Week 7-8)**

1. **Performance optimization:**
   ```python
   # app/utils/cache.py
   import redis
   import json
   from functools import wraps
   
   class RedisCache:
       def __init__(self, redis_url: str):
           self.redis_client = redis.from_url(redis_url)
       
       def cache_query(self, ttl: int = 3600):
           """Decorator to cache query results"""
           def decorator(func):
               @wraps(func)
               async def wrapper(query: str, *args, **kwargs):
                   cache_key = f"filter_query:{query}"
                   cached = self.redis_client.get(cache_key)
                   
                   if cached:
                       return json.loads(cached)
                   
                   result = await func(query, *args, **kwargs)
                   self.redis_client.setex(
                       cache_key, ttl, json.dumps(result)
                   )
                   return result
               return wrapper
           return decorator
   ```

2. **Monitoring & Metrics:**
   ```python
   # app/utils/metrics.py
   from prometheus_client import Counter, Histogram
   
   query_counter = Counter('filter_queries_total', 'Total queries')
   query_duration = Histogram('filter_query_duration_seconds', 
                             'Query processing time')
   cache_hits = Counter('cache_hits_total', 'Cache hit count')
   ```

3. **User feedback loop:**
   - Add "Was this helpful?" endpoint
   - Collect filter acceptance rates
   - A/B test different approaches

---

## 📊 API Endpoints

### **POST /api/filter/analyze-query**

**Request:**
```json
{
  "query": "railway signaling expert with ERTMS and SCADE experience",
  "options": {
    "maxFiltersPerCategory": 10,
    "minConfidence": 0.6
  }
}
```

**Response:**
```json
{
  "query": "railway signaling expert with ERTMS and SCADE experience",
  "reducedFilters": {
    "tool": ["SCADE", "Scade", "EN50128", "EN50129", "TestLink", "Prover"],
    "environnement-domain": ["Railway"],
    "environnement-context": {
      "Railway": ["High Speed Lines", "Main Lines", "Metro"]
    },
    "domain-competence": {
      "Railway": ["Signalling"]
    },
    "domain-speciality": {
      "Signalling": ["ERTMS", "CBTC", "Interlocking (IXL)"]
    },
    "domain-specificity": {
      "ERTMS": [
        "ETCS ( European Train Control System)",
        "RBC (Radio Block Center)",
        "EVC (European Vital Computer)"
      ]
    },
    "experience": ["Experts", "Seniors", "Confirmed"],
    "engineering-skill": [
      "System Engineering engineer",
      "Electrical and Electronic Engineering"
    ]
  },
  "confidence": {
    "tool": 0.89,
    "environnement-domain": 0.97,
    "domain-competence": 0.94,
    "domain-speciality": 0.92,
    "experience": 0.71
  },
  "reasoning": {
    "tool": "SCADE is commonly used for ERTMS safety-critical systems",
    "environnement-domain": "Query explicitly mentions 'railway'",
    "domain-speciality": "ERTMS is a signalling specialization"
  },
  "totalReduction": "87%",
  "processingTime": "234ms"
}
```

### **POST /api/filter/feedback**

**Request:**
```json
{
  "query": "railway ERTMS expert",
  "recommendedFilters": {...},
  "userSelectedFilters": {...},
  "wasHelpful": true,
  "comments": "Perfect suggestions!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Feedback recorded for future improvements"
}
```

---

## 🧪 Testing Strategy

### **Unit Tests**
```python
# tests/test_query_analyzer.py
import pytest
from app.services.query_analyzer import QueryAnalyzer

def test_keyword_extraction():
    analyzer = QueryAnalyzer()
    keywords = analyzer.extract_keywords("railway ERTMS expert")
    assert "railway" in keywords
    assert "ERTMS" in keywords
    assert "expert" in keywords

# tests/test_embedding_service.py
def test_embedding_generation():
    from app.services.ollama_client import OllamaClient
    client = OllamaClient()
    embedding = client.generate_embedding("test query")
    assert len(embedding) == 768  # nomic-embed-text dimension

# tests/test_filter_matcher.py
def test_fuzzy_matching():
    from app.services.filter_matcher import FilterMatcher
    matcher = FilterMatcher()
    score = matcher.fuzzy_match_score("ERTMS", "ETCS")
    assert score > 0.3
```

### **Integration Tests**
```python
# tests/test_filter_routes.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_analyze_query_endpoint():
    response = client.post(
        "/api/filter/analyze-query",
        json={"query": "railway ERTMS expert"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "reducedFilters" in data
    assert len(data["reducedFilters"]["tool"]) < 20
    assert data["confidence"]["tool"] > 0.6

def test_invalid_query():
    response = client.post(
        "/api/filter/analyze-query",
        json={"query": ""}
    )
    assert response.status_code == 422  # Validation error
```

### **Run Tests**
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio httpx

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_filter_routes.py -v
```

### **Sample Test Queries**
```python
# tests/fixtures/test_queries.py
TEST_QUERIES = [
    {
        "query": "railway signaling expert with ERTMS",
        "expected_domain": "Railway",
        "expected_tools": ["SCADE", "EN50128", "EN50129"]
    },
    {
        "query": "nuclear power plant instrumentation engineer",
        "expected_domain": "Energy",
        "expected_context": "Nucléaire"
    },
    {
        "query": "metro automation CBTC specialist",
        "expected_domain": "Railway",
        "expected_speciality": "CBTC"
    },
    {
        "query": "high-speed rail project manager with RAMS",
        "expected_intervention": "Project Management"
    },
    {
        "query": "embedded systems developer for rolling stock",
        "expected_tools": ["Python", "C", "C++"]
    },
    {
        "query": "Python developer for energy smart grid",
        "expected_domain": "Energy",
        "expected_tools": ["Python"]
    },
    {
        "query": "civil engineer for tunnel infrastructure",
        "expected_speciality": "Fixed Installations / Civil Engineering"
    },
    {
        "query": "cybersecurity expert for railway systems",
        "expected_skill": "Cybersecurity Engineer"
    }
]
```

---

## 📦 Python Dependencies (requirements.txt)

```txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# HTTP Client
requests==2.31.0
httpx==0.25.2

# Database
pymongo==4.6.0
motor==3.3.2  # Async MongoDB driver
redis==5.0.1

# ML & NLP
numpy==1.26.2
scikit-learn==1.3.2
sentence-transformers==2.2.2  # Optional: for better embeddings

# Utilities
python-dotenv==1.0.0
python-multipart==0.0.6

# Monitoring
prometheus-client==0.19.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
```

---

## 🐳 Dockerfile for Python Service

```dockerfile
# ai-filter-service/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

---

## 🚀 FastAPI Application Entry Point

```python
# ai-filter-service/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import filter_routes, health_routes
from app.config import settings

app = FastAPI(
    title="Smart Filter Selector",
    description="Intelligent filter recommendation using ML/AI",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_routes.router, tags=["health"])
app.include_router(filter_routes.router, prefix="/api", tags=["filters"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 Starting Smart Filter Selector Service...")
    print(f"📊 Ollama URL: {settings.OLLAMA_URL}")
    print(f"🗄️  MongoDB URL: {settings.MONGODB_URL}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Shutting down Smart Filter Selector Service...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## ⚙️ Configuration

```python
# ai-filter-service/app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Ollama Configuration
    OLLAMA_URL: str = "http://ollama:11434"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_LLM_MODEL: str = "llama3.2"
    
    # Database Configuration
    MONGODB_URL: str = "mongodb://mongodb:27017/"
    MONGODB_DB_NAME: str = "smart_filter"
    REDIS_URL: str = "redis://redis:6379"
    
    # Application Configuration
    MAX_FILTERS_PER_CATEGORY: int = 10
    MIN_CONFIDENCE_THRESHOLD: float = 0.6
    CACHE_TTL: int = 3600  # 1 hour
    
    # Model Configuration
    EMBEDDING_DIMENSION: int = 768
    TOP_K_SIMILARITY: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

---

## 📝 Environment Variables

```bash
# ai-filter-service/.env.example
OLLAMA_URL=http://ollama:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_LLM_MODEL=llama3.2

MONGODB_URL=mongodb://mongodb:27017/
MONGODB_DB_NAME=smart_filter
REDIS_URL=redis://redis:6379

MAX_FILTERS_PER_CATEGORY=10
MIN_CONFIDENCE_THRESHOLD=0.6
CACHE_TTL=3600
```

## 📈 Performance Metrics

### **Target Metrics**
- **Response Time:** < 500ms for query analysis
- **Accuracy:** > 80% user acceptance of recommended filters
- **Reduction Rate:** 70-90% fewer filter options displayed
- **Confidence Score:** > 0.7 for primary filters

### **Monitoring Dashboard**
- Query processing time (p50, p95, p99)
- Cache hit rate (Redis)
- Ollama API latency
- User feedback scores
- Most common queries
- Filter selection patterns

---

## 🔒 Security Considerations

1. **Input Validation:** Sanitize user queries to prevent injection
2. **Rate Limiting:** Limit API requests per user/IP
3. **Ollama Access:** Keep Ollama service internal (not exposed)
4. **Data Privacy:** Don't log sensitive consultant information
5. **CORS:** Configure proper CORS policies for frontend

---

## 🚀 Future Enhancements

1. **Multi-language Support:** French + English query handling with language detection
2. **Voice Input:** Speech-to-text integration
3. **Auto-complete:** Real-time filter suggestions while typing
4. **Saved Searches:** Store frequent query patterns per user
5. **Filter Templates:** Pre-built filter combinations for common searches
6. **Analytics Dashboard:** Visualize query patterns and trends (Python/Streamlit)
7. **Fine-tuning:** Train custom embedding model on domain-specific data
8. **Explainable AI:** Show detailed reasoning for filter selection
9. **Batch Processing:** Analyze multiple queries in parallel
10. **gRPC Support:** Add gRPC endpoints for high-performance applications

---

## 📚 Resources

### **Python & FastAPI**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [PyMongo Documentation](https://pymongo.readthedocs.io/)

### **Ollama Documentation**
- [Ollama API Reference](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Ollama Models Library](https://ollama.com/library)
- [Ollama Python Client](https://github.com/ollama/ollama-python)

### **Embedding Models**
- `nomic-embed-text`: 768-dim embeddings, best for semantic search
- `all-minilm`: 384-dim, lightweight alternative
- `mxbai-embed-large`: 1024-dim, highest quality

### **LLM Models**
- `llama3.2:3b`: Fast, good for simple tasks (~3GB)
- `mistral:7b`: Better reasoning, moderate speed (~7GB)
- `llama3.1:8b`: Best balance of quality and speed (~8GB)

### **Machine Learning Libraries**
- [NumPy Documentation](https://numpy.org/doc/)
- [scikit-learn Documentation](https://scikit-learn.org/)
- [Sentence Transformers](https://www.sbert.net/)


### **Development Setup**

```bash
# Clone repo
git clone https://github.com/ikos-lab/smart-filter-selector.git
cd smart-filter-selector

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Dev dependencies

# Run tests
pytest tests/ -v --cov=app

# Format code
black app/
isort app/

# Lint code
flake8 app/
mypy app/

# Run locally (without Docker)
uvicorn app.main:app --reload
```

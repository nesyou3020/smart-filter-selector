# Smart Filter Selector - Architecture & Concepts Guide

## 📚 Table of Contents
1. [Core Concepts](#core-concepts)
2. [What are Embeddings?](#what-are-embeddings)
3. [How the LLM Works](#how-the-llm-works)
4. [Semantic Search Explained](#semantic-search-explained)
5. [Filter Generation Pipeline](#filter-generation-pipeline)
6. [System Architecture](#system-architecture)
7. [Data Flow Diagram](#data-flow-diagram)
8. [Backend/Frontend Workflow](#backendfrontend-workflow)

---

## Core Concepts

### What is the Smart Filter Selector?

Imagine you have a massive catalog of products, documents, or items with many possible filters (categories, tags, attributes). Usually, users have to manually check boxes and tick options:

```
[ ] Railway
[ ] Signalling
[ ] ERTMS
[ ] Energy
[ ] MATLAB
... (100+ more options)
```

**The Problem:** Users don't know which filters are relevant to their search.

**The Solution:** Smart Filter Selector intelligently **suggests which filters are most relevant** based on what the user types in plain English:

```
User types: "I'm working on ERTMS signaling systems for high-speed trains"
↓
System responds: "Here are the most relevant filters for you:"
- Railway ✓
- Signalling ✓
- ERTMS ✓
- High Speed Lines ✓
```

### How Does It Work (High-Level)?

The system uses **three powerful AI techniques** working together:

1. **Embeddings** → Convert text into numbers so we can find similar concepts
2. **Semantic Search** → Find filters similar to what the user is asking about
3. **LLM (Large Language Model)** → Use AI to refine the selection and understand context

---

## What are Embeddings?

### What is an Embedding?

An **embedding** is a way to convert **text into numbers**. Think of it as:

**Human-readable text:**
```
"Railway signaling system"
```

**Computer-friendly embedding (vector):**
```
[0.234, -0.891, 0.156, 0.423, -0.234, 0.567, ..., 0.123]
     ↑       ↑       ↑       ↑      ↑      ↑         ↑
(300+ numbers representing the meaning of the text)
```

### Why Embeddings?

Computers can't directly compare text like "ERTMS" with "European Railway Management System". But they **can** compare numbers!

**Key Insight:** Words with similar meanings will have **similar numerical patterns**.

```
Embedding of "ERTMS" ≈ [0.1, 0.5, -0.3, ...]
Embedding of "signaling" ≈ [0.15, 0.48, -0.29, ...]
                                     ↑
                              (Very similar!)

Embedding of "ice cream" ≈ [0.9, -0.2, 0.7, ...]
                                    ↑
                           (Very different from ERTMS)
```

### How Are Embeddings Created?

The smart-filter-selector uses **Ollama** (a local AI model) to generate embeddings:

1. Take a filter name + description: `"ERTMS - European Railway Management System"`
2. Send it to an embedding model (like `mxbai-embed-large`)
3. Get back a vector of ~1024 numbers
4. Store it in **ChromaDB** (a vector database)

```python
# How it works in code:
filter_text = "Item: ERTMS\nCategory: Signalling\nDescription: European Railway Management System"
embedding = ollama_client.generate_embedding(filter_text)
# Result: [0.234, -0.891, 0.156, ..., 0.123] (1024 numbers)
```

### Why Pre-Compute Embeddings?

Instead of computing embeddings on-the-fly every time, the system:

1. **Pre-computes** embeddings for all filters once (during setup)
2. **Stores** them in ChromaDB (persistent database)
3. **Reuses** them for every query (super fast!)

**Example Timeline:**
- Setup (once): Generate 500 filters → 500 embeddings → 5 minutes
- Query (every time): Compare user query → < 1 second!

---

## How the LLM Works

### What is an LLM?

An **LLM (Large Language Model)** is an AI that understands and generates human language. Think of it as a very smart assistant that can:

- Read and understand text
- Make intelligent decisions
- Explain its reasoning
- Follow instructions precisely

### How is the LLM Used in Smart Filter Selector?

The LLM plays **two critical roles:**

#### **Stage 1: Embedding Search (Fast but Dumb)**
The embedding system finds candidates: "Here are 20 filters that might be relevant"

**Problem:** This includes false positives!
```
Query: "ERTMS signaling"
Embedding search returns:
- ERTMS ✓ (correct)
- Signalling ✓ (correct)
- E-mail systems ✗ (wrong! just similar letters)
- Energy systems ✗ (wrong! just similar meaning)
```

#### **Stage 2: LLM Refinement (Slower but Smart)**
The LLM reads the candidates and **intelligently filters** them:

```
Input to LLM:
"User is asking about: ERTMS signaling
Candidates: [ERTMS, Signalling, E-mail systems, Energy systems, ...]"

LLM thinks: "The user is asking about railway signaling systems. 
ERTMS and Signalling are relevant. E-mail and Energy are not related."

Output:
- ERTMS (confidence: 0.95)
- Signalling (confidence: 0.90)
```

### How the LLM is Prompted

The system uses **prompt engineering** - carefully crafted instructions to guide the LLM:

```python
template = """
You are an expert filter recommendation system.

User Query: "{user_query}"
Available filter candidates: {candidates}

Your task:
1. Analyze the user query
2. Select ONLY the most relevant filters
3. Provide confidence scores (0-1)
4. Explain your reasoning

IMPORTANT: Do NOT invent new categories. 
Use ONLY the exact names from the candidates list.
"""
```

**Why this matters:** The prompt tells the LLM exactly what we want, preventing it from making up filters!

---

## Semantic Search Explained

### What is Semantic Search?

**Semantic** = "meaning-based"

**Semantic Search** = Finding things based on **meaning**, not just keyword matching.

### Example: Regular Search vs Semantic Search

**Query:** "I work with train safety systems"

#### Regular Search (Keyword-based)
```
Does it contain "train"? Does it contain "safety"?
Results: 
✓ Train (contains "train")
✓ Safety protocols (contains "safety")
✗ ERTMS (doesn't contain either word - WRONG!)
```

#### Semantic Search (Meaning-based)
```
What is the MEANING of this query?
"train safety systems" = railway signaling/safety domain

Compare MEANING with all filters:
✓ Train (related to railways)
✓ Safety protocols (related to safety)
✓ ERTMS (railway safety system!) - CORRECT!
```

### How Semantic Search Works in Smart Filter Selector

```
Step 1: Convert user query to embedding
┌─────────────────────────────────────┐
│ "I work with train safety systems"  │
└─────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────┐
│ [0.234, -0.891, ..., 0.123]         │  (query embedding)
└─────────────────────────────────────┘

Step 2: Compare with all stored filter embeddings
┌──────────────────────────────────────────────┐
│ ERTMS embedding: [0.240, -0.885, ...]        │ similarity: 0.92 ✓
│ Signalling embedding: [0.238, -0.892, ...]   │ similarity: 0.91 ✓
│ Ice cream embedding: [0.900, -0.100, ...]    │ similarity: 0.05 ✗
└──────────────────────────────────────────────┘

Step 3: Sort by similarity and take top-20
Result: [ERTMS, Signalling, Railway, ...]
```

### The Similarity Calculation: Cosine Similarity

How do we measure how similar two embeddings are?

```python
def cosine_similarity(vec_a, vec_b):
    """Compare two vectors by angle between them"""
    dot_product = sum(a*b for a,b in zip(vec_a, vec_b))
    magnitude_a = sqrt(sum(x**2 for x in vec_a))
    magnitude_b = sqrt(sum(x**2 for x in vec_b))
    
    return dot_product / (magnitude_a * magnitude_b)
    # Returns 0 (opposite) to 1 (identical)
```

**Intuition:** Two vectors pointing in the same direction = similar meaning!

---

## Filter Generation Pipeline

### The Complete Pipeline: 4 Stages

The system processes every query through 4 distinct stages:

```
┌─────────────────────────────────────────────────────────┐
│ STAGE 0: Language Detection & Translation               │
├─────────────────────────────────────────────────────────┤
│ Input:  "Je travaille sur un système ERTMS"             │
│ Detect: French                                           │
│ Translate: "I'm working on an ERTMS system"             │
│ Output: English query                                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ STAGE 1: Embedding-Based Fast Search                    │
├─────────────────────────────────────────────────────────┤
│ 1. Convert query to embedding                           │
│ 2. Calculate cosine similarity with all 500 filters     │
│ 3. Return top-20 most similar filters                   │
│ Time: ~100ms                                             │
│ Output: [ERTMS, Signalling, Railway, Energy, ...]       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ STAGE 2: LLM-Based Intelligent Refinement               │
├─────────────────────────────────────────────────────────┤
│ 1. Send candidates + user query to LLM                  │
│ 2. LLM analyzes context and selects best matches        │
│ 3. LLM provides confidence scores per category          │
│ 4. LLM explains reasoning                               │
│ Time: ~2 seconds (LLM is slower)                        │
│ Output: {                                                │
│   "filters": ["ERTMS", "Signalling"],                   │
│   "confidence": {"ERTMS": 0.95, "Signalling": 0.92},    │
│   "reasoning": "User mentioned ERTMS and signaling..."  │
│ }                                                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ STAGE 3: Level Detection (Expertise & Language)         │
├─────────────────────────────────────────────────────────┤
│ 1. LLM analyzes user experience level                   │
│ 2. Detects professional seniority (Junior/Senior/Expert)│
│ 3. Detects language proficiency (A1-C2 CEFR levels)    │
│ Time: ~1 second                                         │
│ Output: {                                                │
│   "experience": ["Confirmed", "Senior"],                │
│   "tool-expertise": "advanced",                          │
│   "language-level": "C1"                                 │
│ }                                                        │
└─────────────────────────────────────────────────────────┘
```

### Why 4 Stages?

| Stage | Purpose | Speed | Intelligence |
|-------|---------|-------|--------------|
| 0 | Make system multilingual | Instant | Low |
| 1 | Fast candidate finding | 100ms | Medium |
| 2 | Smart filtering | 2sec | **High** |
| 3 | Understand user context | 1sec | High |

**Strategy:** Use fast methods first, then refine with slow but smart methods!

---

## System Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Frontend)                         │
│  Web Interface / Mobile App / API Consumer                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    HTTP POST /analyze-query
                             │
┌─────────────────────────────────────────────────────────────────┐
│                   FLASK REST API SERVER                          │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         filter_routes.py (API Endpoint)                  │   │
│  │  - POST /api/filter/analyze-query                        │   │
│  │  - GET /health (health check)                            │   │
│  └────────────────┬─────────────────────────────────────────┘   │
│                   │                                              │
│  ┌────────────────▼─────────────────────────────────────────┐   │
│  │     HybridFilterSelector (Main Orchestrator)             │   │
│  │  - Coordinates all 4 stages                              │   │
│  │  - Manages input/output flow                             │   │
│  └──┬─────────┬──────────┬────────┬──────────────────────────┘   │
│     │         │          │        │                             │
│  ┌──▼──┐  ┌──▼──┐    ┌──▼──┐  ┌──▼──────┐                       │
│  │Stage│  │Stage│    │Stage│  │Stage 3: │                       │
│  │  0: │  │  1: │    │  2: │  │ Level   │                       │
│  │Trans│  │Embed│    │ LLM │  │Detector │                       │
│  │lation│ │ding │    │Refin│  │         │                       │
│  │     │  │     │    │ement│  │         │                       │
│  │     │  │     │    │     │  │         │                       │
│  └─────┘  └──┬──┘    └──┬──┘  └────┬────┘                       │
│             │           │          │                             │
│             ▼           ▼          ▼                             │
│    ┌─────────────────────────────────────┐                      │
│    │   EmbeddingService (Vector DB)      │                      │
│    │   - ChromaDB (persistent storage)   │                      │
│    │   - 500+ filter embeddings          │                      │
│    │   - Cosine similarity search        │                      │
│    └─────────────────────────────────────┘                      │
│             │                                                    │
│    ┌────────▼──────────────────────────────┐                    │
│    │   OllamaClient (Local AI Models)      │                    │
│    │   - mxbai-embed-large (embeddings)    │                    │
│    │   - llama3.1:8b (LLM for refinement)  │                    │
│    └─────────────────────────────────────┘                      │
│             │                                                    │
└─────────────┼────────────────────────────────────────────────────┘
              │
┌─────────────▼────────────────────────────────────────────────────┐
│         OLLAMA SERVER (Local AI Runtime)                          │
│  Runs embedding models and LLM inference                          │
│  Can be on same machine or remote                                 │
└───────────────────────────────────────────────────────────────────┘
```

### Class Structure

```
HybridFilterSelector
├── embedding_service: EmbeddingService
│   ├── ollama_client: OllamaClient
│   ├── chroma_client: ChromaDB
│   └── filter_embeddings: List[Dict]
├── llm_service: LLMService
│   ├── llm: Ollama (LangChain)
│   └── prompt: PromptTemplate
├── translation_service: TranslationService
│   ├── GoogleTranslator
│   └── LangDetect
└── level_detector: LevelDetector
    └── llm: Ollama (LangChain)
```

---

## Data Flow Diagram

### Query Processing Data Flow

```
User Input
    │
    ├─ Query: "I'm working on ERTMS signaling for high-speed trains"
    │
    ▼
STAGE 0: Translation Service
    ├─ Detects language: English
    ├─ Check if translation needed: No
    └─ Output: {
         "detectedLanguage": "en",
         "translatedQuery": "I'm working on ERTMS signaling for high-speed trains",
         "isTranslated": false
       }
    │
    ▼
STAGE 1: Embedding Service
    ├─ Clean query text:
    │  "I'm working on ERTMS signaling for high-speed trains"
    │  → "working ertms signaling high speed trains"
    │
    ├─ Generate embedding for cleaned query
    │  → [0.234, -0.891, 0.156, ..., 0.123] (1024 numbers)
    │
    ├─ Compare with all 500 filter embeddings using cosine similarity
    │  ├─ ERTMS: similarity = 0.92
    │  ├─ Signalling: similarity = 0.91
    │  ├─ Railway: similarity = 0.88
    │  ├─ High Speed Lines: similarity = 0.87
    │  └─ [16 more candidates...]
    │
    └─ Output: Top-20 candidates sorted by similarity score
    │
    ▼
STAGE 2: LLM Service
    ├─ Format prompt with:
    │  ├─ Original user query
    │  └─ Top-20 candidates from embedding search
    │
    ├─ Send to LLM with instructions:
    │  "Select ONLY the most relevant filters.
    │   Provide confidence scores (0-1).
    │   Explain your reasoning."
    │
    ├─ LLM analyzes and responds with structured JSON:
    │  {
    │    "reducedFilters": [
    │      {"name": "ERTMS", "category": "Signalling", "score": 0.95},
    │      {"name": "Signalling", "category": "Signalling", "score": 0.92},
    │      {"name": "Railway", "category": "Infrastructure", "score": 0.88},
    │      {"name": "High Speed Lines", "category": "Infrastructure", "score": 0.87}
    │    ],
    │    "confidence": {
    │      "Signalling": 0.93,
    │      "Infrastructure": 0.87
    │    },
    │    "reasoning": {
    │      "Signalling": "User explicitly mentioned ERTMS signaling systems",
    │      "Infrastructure": "High-speed trains require specific infrastructure"
    │    }
    │  }
    │
    └─ Output: Refined filter list with confidence and reasoning
    │
    ▼
STAGE 3: Level Detector
    ├─ Analyze user query for indicators:
    │  ├─ Experience level: "working on" suggests Confirmed/Senior level
    │  ├─ Tool expertise: "ERTMS" suggests advanced knowledge
    │  └─ Language level: English usage suggests B2-C1 proficiency
    │
    └─ Output: {
         "detectedLevels": {
           "experience": ["Confirmed", "Senior"],
           "tool-expertise": "advanced"
         },
         "confidence": {
           "experience": 0.85,
           "tool-expertise": 0.90
         },
         "reasoning": "User discusses advanced railway systems confidently"
       }
    │
    ▼
Final Response to Client
    {
      "originalQuery": "I'm working on ERTMS signaling for high-speed trains",
      "translatedQuery": "...",
      "detectedLanguage": "en",
      "reducedFilters": [
        {"name": "ERTMS", "category": "Signalling", ...},
        {"name": "Signalling", "category": "Signalling", ...},
        {"name": "Railway", "category": "Infrastructure", ...},
        {"name": "High Speed Lines", "category": "Infrastructure", ...}
      ],
      "confidence": {...},
      "reasoning": {...},
      "detectedLevels": {...},
      "processingTime": "3.24s",
      "stages": {
        "translation": "0.05s",
        "embedding_search": "0.10s",
        "llm_refinement": "2.50s",
        "level_detection": "0.59s"
      }
    }
```

---

## Backend/Frontend Workflow

### End-to-End User Journey

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE (Frontend)                 │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Text Input                                         │    │
│  │  "I'm working on ERTMS signaling systems"          │    │
│  │                                                     │    │
│  │  [Submit Query Button]                              │    │
│  └─────────────────────────┬───────────────────────────┘    │
│                            │                                  │
└────────────────────────────┼──────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
    ┌──────────────────┐        ┌──────────────────┐
    │ Spinner/Loading  │        │ Disable Submit   │
    │ "Processing..."  │        │ Button           │
    └──────────────────┘        └──────────────────┘
              │                             │
              └──────────────┬──────────────┘
                             │
┌────────────────────────────┼──────────────────────────────────┐
│                            │                                   │
│                   Backend Processing                           │
│                            │                                   │
│  ┌──────────────────────────▼───────────────────────────┐    │
│  │ Route Handler: POST /api/filter/analyze-query        │    │
│  │ - Validate JSON request                             │    │
│  │ - Extract query and options                         │    │
│  └───────────────────┬────────────────────────────────┘    │
│                      │                                       │
│  ┌───────────────────▼────────────────────────────────┐    │
│  │ HybridFilterSelector.select_filters()              │    │
│  │ (4-stage processing pipeline)                      │    │
│  └───────────────────┬────────────────────────────────┘    │
│                      │                                       │
│  ┌───────────────────▼────────────────────────────────┐    │
│  │ Stage 0: Translation                               │    │
│  │ - Detect language → English                        │    │
│  │ - No translation needed                            │    │
│  └───────────────────┬────────────────────────────────┘    │
│                      │                                       │
│  ┌───────────────────▼────────────────────────────────┐    │
│  │ Stage 1: Embedding Search                          │    │
│  │ - Clean query text                                 │    │
│  │ - Convert to embedding                             │    │
│  │ - Find 20 most similar filters                      │    │
│  └───────────────────┬────────────────────────────────┘    │
│                      │                                       │
│  ┌───────────────────▼────────────────────────────────┐    │
│  │ Stage 2: LLM Refinement                            │    │
│  │ - Build prompt with query + candidates            │    │
│  │ - Send to LLM for intelligent selection            │    │
│  │ - Get confidence scores and reasoning              │    │
│  └───────────────────┬────────────────────────────────┘    │
│                      │                                       │
│  ┌───────────────────▼────────────────────────────────┐    │
│  │ Stage 3: Level Detection                           │    │
│  │ - Detect user expertise level                      │    │
│  │ - Analyze tool proficiency                         │    │
│  │ - Identify language proficiency                    │    │
│  └───────────────────┬────────────────────────────────┘    │
│                      │                                       │
│  ┌───────────────────▼────────────────────────────────┐    │
│  │ Compile Results                                    │    │
│  │ - Combine all outputs                              │    │
│  │ - Add timing information                           │    │
│  └───────────────────┬────────────────────────────────┘    │
│                      │                                       │
└──────────────────────┼──────────────────────────────────────┘
                       │
                 HTTP 200 OK
                   (JSON Response)
                       │
┌──────────────────────┼──────────────────────────────────────┐
│                      │                                       │
│                Frontend Processing                           │
│                      │                                       │
│  ┌───────────────────▼────────────────────────────────┐    │
│  │ Parse JSON Response                                │    │
│  │ - Extract filter recommendations                   │    │
│  │ - Extract confidence scores                        │    │
│  │ - Extract reasoning                                │    │
│  └───────────────────┬────────────────────────────────┘    │
│                      │                                       │
│  ┌───────────────────▼────────────────────────────────┐    │
│  │ Display Results                                    │    │
│  │                                                    │    │
│  │ "Recommended Filters:"                             │    │
│  │ ✓ ERTMS [95% confidence]                          │    │
│  │ ✓ Signalling [92% confidence]                      │    │
│  │ ✓ Railway [88% confidence]                         │    │
│  │ ✓ High Speed Lines [87% confidence]               │    │
│  │                                                    │    │
│  │ "Why These Filters?"                               │    │
│  │ "You asked about ERTMS signaling systems. These   │    │
│  │  filters are the most relevant for your query."   │    │
│  └───────────────────┬────────────────────────────────┘    │
│                      │                                       │
│  ┌───────────────────▼────────────────────────────────┐    │
│  │ User Actions                                       │    │
│  │ - Click checkboxes to select filters              │    │
│  │ - Apply filters to search                         │    │
│  │ - Modify and refine search                         │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### API Request/Response Example

**Request:**
```json
POST /api/filter/analyze-query
Content-Type: application/json

{
  "query": "I'm working on ERTMS signaling systems for high-speed trains",
  "options": {
    "maxFiltersPerCategory": 10,
    "minConfidence": 0.6
  }
}
```

**Response:**
```json
{
  "originalQuery": "I'm working on ERTMS signaling systems for high-speed trains",
  "translatedQuery": "I'm working on ERTMS signaling systems for high-speed trains",
  "detectedLanguage": "en",
  "translationConfidence": 1.0,
  "isTranslated": false,
  
  "reducedFilters": [
    {
      "name": "ERTMS",
      "category": "Signalling",
      "subcategory": "",
      "score": 0.95
    },
    {
      "name": "Signalling",
      "category": "Signalling",
      "subcategory": "",
      "score": 0.92
    },
    {
      "name": "Railway",
      "category": "Infrastructure",
      "subcategory": "",
      "score": 0.88
    }
  ],
  
  "confidence": {
    "Signalling": 0.93,
    "Infrastructure": 0.87
  },
  
  "reasoning": {
    "Signalling": "User explicitly mentioned ERTMS signaling systems, indicating high relevance to this category.",
    "Infrastructure": "High-speed trains require infrastructure planning and design, making this category relevant."
  },
  
  "detectedLevels": {
    "experience": ["Confirmed", "Senior"],
    "tool-expertise": "advanced"
  },
  
  "levelConfidence": {
    "experience": 0.85,
    "tool-expertise": 0.90
  },
  
  "levelReasoning": "User demonstrates advanced knowledge of railway systems and professional experience in the field.",
  
  "processingTime": "3.24s",
  "stages": {
    "translation": "0.05s",
    "embedding_search": "0.10s",
    "llm_refinement": "2.50s",
    "level_detection": "0.59s"
  }
}
```

---

## Key Takeaways

### The 4-Stage Pipeline (Simplified)

| Stage | Input | Process | Output | Speed | Use |
|-------|-------|---------|--------|-------|-----|
| **0** | Any language query | Translate to English | English query | Fast | Enable multilingual support |
| **1** | English query | Convert to embedding, find similar filters | 20 candidates | Fast | Quick filtering |
| **2** | 20 candidates | Use LLM to intelligently select | 5 best filters | Slow | Smart, context-aware selection |
| **3** | User query | Analyze expertise indicators | User levels | Slow | Understand user background |

### Why This Design?

1. **Fast First**: Embedding search (100ms) eliminates 90% of filters quickly
2. **Smart Second**: LLM (2 seconds) intelligently refines the remaining 20
3. **Context Third**: Level detection helps personalize the experience
4. **Hybrid**: Combines speed of embeddings with intelligence of LLM

### The Math Behind It All

- **Embeddings**: Convert text to numbers (1024-dimensional vectors)
- **Similarity**: Cosine of angle between vectors (0 = opposite, 1 = identical)
- **LLM**: Neural network trained on billions of words to understand meaning
- **Prompt Engineering**: Guide the LLM's reasoning with carefully crafted instructions

---

## Further Reading

- **Embeddings**: https://en.wikipedia.org/wiki/Word_embedding
- **Cosine Similarity**: https://en.wikipedia.org/wiki/Cosine_similarity
- **LLMs**: https://en.wikipedia.org/wiki/Large_language_model
- **ChromaDB**: https://www.trychroma.com/ (Vector database documentation)
- **Ollama**: https://ollama.ai/ (Local AI models)


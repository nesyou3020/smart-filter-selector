# Smart Filter Selector

## Project Overview
The Smart Filter Selector is a Python-based microservice designed to intelligently select filters using embeddings and large language models (LLMs). It is built with Flask and integrates various services for embedding generation, hybrid selection, and language translation.

## Features
- Embedding-based filter selection.
- LLM-based refinement for intelligent filtering.
- Language detection and translation.
- Expertise/proficiency level detection.
- Modular architecture for scalability and maintainability.

## Installation

### Prerequisites
- Python >= 3.11
- Ollama server for embeddings and LLMs

### Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd smart-filter-selector
   ```

2. Install dependencies using `uv`:
   ```bash
   uv sync
   ```

3. Configure environment variables in `app/config.py`:
   - Update parameters such as `OLLAMA_URL` and `FLASK_PORT` as needed.

4. Start Ollama servers.

5. Generate embeddings:
   ```bash
   uv run scripts/generate_embeddings.py
   ```
6. Docker
   ```bash
   docker build -t smart-filter-selector .
   docker run --name smart_fs_ms -p 8000:8000 smart-filter-selector 
   ```
## Usage

### Running the Service
Start the Flask application:
```bash
uv run run.py
```

### API Endpoints
- **Health Check**: `GET /health`
- **Analyze Query**: `POST /api/filter/analyze-query`
  - Request Body:
    ```json
    {
      "query": "Your natural language query",
      "options": {
        "maxFiltersPerCategory": 10,
        "minConfidence": 0.6
      }
    }
    ```
- **List Embeddings**: `GET /api/filter/embeddings`

## Project Structure
```
smart-filter-selector/
├── app/
│   ├── config.py          # Configuration settings
│   ├── main.py            # Flask app creation and setup
│   ├── models/            # Request and response models
│   ├── routes/            # API routes
│   ├── services/          # Core services (embedding, LLM, etc.)
│   └── utils/             # Utility modules
├── data/                  # Data files (e.g., levels.json, embeddings)
├── scripts/               # Scripts for generating embeddings
├── run.py                 # Entry point for the Flask app
├── test_api.py            # API testing script
└── pyproject.toml         # Project dependencies and metadata
```

## Key Components

### Services
- **Embedding Service**: Manages embeddings and similarity search.
- **Hybrid Selector**: Combines embeddings and LLM for filter selection.
- **Translation Service**: Detects and translates non-English queries.
- **Level Detector**: Identifies expertise/proficiency levels.

### Utilities
- **Filter Loader**: Loads and manages filter configuration data.
- **Similarity**: Computes cosine similarity between vectors.



## Precision: test_queries.py
```text
$ uv run test/test_queries.py
INFO:__main__:🔍 Running Smart Filter Selector tests, Number of tests: 30...

INFO:__main__:🧠 [1] Testing query (en): I’m working on a project related to train signaling systems.
INFO:__main__:   ✅ Expected: ['Railway', 'Signalling']
INFO:__main__:   🧩 Detected: ['Railway', 'Interlocking (IXL)', 'Signalling', 'Train detection', 'ERTMS', 'CBTC']
INFO:__main__:   📊 Precision: 0.33, Recall: 1.0, F1: 0.5

INFO:__main__:🧠 [2] Testing query (fr): Je travaille sur un projet de gestion d’énergie nucléaire.
INFO:__main__:   ✅ Expected: ['Energy', 'Nucléaire']
INFO:__main__:   🧩 Detected: ['Renewable Energie', 'Energy', 'monitoring & control and instrumentation', 'Nucléaire']
INFO:__main__:   📊 Precision: 0.5, Recall: 1.0, F1: 0.67

INFO:__main__:🧠 [3] Testing query (es): Estoy desarrollando una aplicación para líneas de alta velocidad.
INFO:__main__:   ✅ Expected: ['Railway', 'High Speed Lines']
INFO:__main__:   🧩 Detected: ['Railway', 'Electrical power line', 'High Speed Lines', 'Level Crossings', 'High Voltage', 'Infrastructure', 'Main Lines', 'Catenary']
INFO:__main__:   📊 Precision: 0.25, Recall: 1.0, F1: 0.4

INFO:__main__:🧠 [4] Testing query (en): We are designing an ERTMS signaling system for high-speed trains.
INFO:__main__:   ✅ Expected: ['Railway', 'Signalling', 'ERTMS']
INFO:__main__:   🧩 Detected: ['EN50129', 'Signalling', 'CBTC', 'ERTMS', 'Interlocking (IXL)']
INFO:__main__:   📊 Precision: 0.4, Recall: 0.67, F1: 0.5

INFO:__main__:🧠 [5] Testing query (fr): Le projet concerne un système CBTC pour métro automatique.
INFO:__main__:   ✅ Expected: ['Railway', 'Signalling', 'CBTC', 'Metro']
INFO:__main__:   🧩 Detected: ['Metro', 'Signalling', 'CBTC', 'Railway']
INFO:__main__:   📊 Precision: 1.0, Recall: 1.0, F1: 1.0

INFO:__main__:🧠 [6] Testing query (es): Nuestro trabajo incluye el desarrollo del enclavamiento IXL.
INFO:__main__:   ✅ Expected: ['Railway', 'Signalling', 'Interlocking (IXL)']
INFO:__main__:   🧩 Detected: ['Signalling', 'Level Crossings', 'Infrastructure', 'Interlocking (IXL)']
INFO:__main__:   📊 Precision: 0.5, Recall: 0.67, F1: 0.57

INFO:__main__:🧠 [7] Testing query (en): We use MATLAB and Simulink for modeling dynamic systems.
INFO:__main__:   ✅ Expected: ['MATLAB', 'SIMULINK']
INFO:__main__:   🧩 Detected: ['Vehicle Dynamics', 'SIMULINK', 'MATLAB', 'Rolling Stock']
INFO:__main__:   📊 Precision: 0.5, Recall: 1.0, F1: 0.67

INFO:__main__:🧠 [8] Testing query (fr): Le modèle est développé sous Scade et testé avec TestLink.
INFO:__main__:   ✅ Expected: ['SCADE', 'TestLink']
INFO:__main__:   🧩 Detected: ['Scade', 'TestLink']
INFO:__main__:   📊 Precision: 1.0, Recall: 1.0, F1: 1.0

INFO:__main__:🧠 [9] Testing query (es): Usamos Primavera y Ps Next para la gestión de proyectos.
INFO:__main__:   ✅ Expected: ['Primavera', 'Ps Next']
INFO:__main__:   🧩 Detected: ['Primavera', 'Ps Next']
INFO:__main__:   📊 Precision: 1.0, Recall: 1.0, F1: 1.0

INFO:__main__:🧠 [10] Testing query (en): Designing low voltage systems for railway stations.
INFO:__main__:   ✅ Expected: ['Railway', 'Low Voltage']
INFO:__main__:   🧩 Detected: ['Railway', 'Building Management System (BMS) / Centralised Technical Management system (CTMS)', 'Low Voltage', 'Radio / Wireless']
INFO:__main__:   📊 Precision: 0.5, Recall: 1.0, F1: 0.67

INFO:__main__:🧠 [11] Testing query (fr): Nous travaillons sur la caténaire pour le train électrique.
INFO:__main__:   ✅ Expected: ['Railway', 'High Voltage', 'Catenary']
INFO:__main__:   🧩 Detected: ['Electrical Systems', 'High Voltage', 'Rolling Stock', 'Traction Systems', 'Catenary']
INFO:__main__:   📊 Precision: 0.4, Recall: 0.67, F1: 0.5

INFO:__main__:🧠 [12] Testing query (es): El proyecto trata de la protección eléctrica de redes de media tensión.
INFO:__main__:   ✅ Expected: ['Energy', 'Transmission And Distribution', 'Electrical Protection']
INFO:__main__:   🧩 Detected: ['Electrical Protection', 'Smart Grid', 'Transmission And Distribution', 'Medium Voltage (MV)']
INFO:__main__:   📊 Precision: 0.5, Recall: 0.67, F1: 0.57

INFO:__main__:🧠 [13] Testing query (en): The software follows the V-model and EN50128 standard.
INFO:__main__:   ✅ Expected: ['Cycle en V', 'EN50128']
INFO:__main__:   🧩 Detected: ['EN50128']
INFO:__main__:   📊 Precision: 1.0, Recall: 0.5, F1: 0.67

INFO:__main__:🧠 [14] Testing query (fr): Le développement est conforme à la norme EN50129 et à la méthode B.
INFO:__main__:   ✅ Expected: ['EN50129', 'Méthode B']
INFO:__main__:   🧩 Detected: ['Méthode B', 'EN50129']
INFO:__main__:   📊 Precision: 1.0, Recall: 1.0, F1: 1.0

INFO:__main__:🧠 [15] Testing query (es): Usamos Git y UML para la documentación del software.
INFO:__main__:   ✅ Expected: ['GIT', 'UML']
INFO:__main__:   🧩 Detected: ['UML', 'GIT']
INFO:__main__:   📊 Precision: 1.0, Recall: 1.0, F1: 1.0

INFO:__main__:🧠 [16] Testing query (en): Performing FMECA and Monte Carlo simulations for risk analysis.
INFO:__main__:   ✅ Expected: ['FMEA - FMECA', 'Monte carlo']
INFO:__main__:   🧩 Detected: ['FMEA - FMECA', 'Monte carlo']
INFO:__main__:   📊 Precision: 1.0, Recall: 1.0, F1: 1.0

INFO:__main__:🧠 [17] Testing query (fr): L’analyse de sécurité est faite selon la norme IEC 61508 et EN50126.
INFO:__main__:   ✅ Expected: ['IEC 61508', 'EN50126']
INFO:__main__:   🧩 Detected: ['EN50126', 'IEC 61508']
INFO:__main__:   📊 Precision: 1.0, Recall: 1.0, F1: 1.0

INFO:__main__:🧠 [18] Testing query (es): Estamos usando Scade y Prover para validar sistemas críticos.
INFO:__main__:   ✅ Expected: ['SCADE', 'Prover']
INFO:__main__:   🧩 Detected: ['SCADE', 'Prover']
INFO:__main__:   📊 Precision: 1.0, Recall: 1.0, F1: 1.0

INFO:__main__:🧠 [19] Testing query (en): We’re designing the civil engineering layout for railway infrastructure.
INFO:__main__:   ✅ Expected: ['Infrastructure', 'Fixed Installations / Civil Engineering']
INFO:__main__:   🧩 Detected: ['Level Crossings', 'Infrastructure', 'Arrangement', 'Hydraulics', 'Fixed Installations / Civil Engineering', 'Geotechnology']
INFO:__main__:   📊 Precision: 0.33, Recall: 1.0, F1: 0.5

INFO:__main__:🧠 [20] Testing query (fr): L’étude porte sur les passages à niveau et la géotechnique ferroviaire.
INFO:__main__:   ✅ Expected: ['Infrastructure', 'Level Crossings', 'Geotechnology']
INFO:__main__:   🧩 Detected: ['Fixed Installations / Civil Engineering', 'Level Crossings', 'Infrastructure', 'Geotechnology']
INFO:__main__:   📊 Precision: 0.75, Recall: 1.0, F1: 0.86

INFO:__main__:🧠 [21] Testing query (es): Incluye el diseño hidráulico de las obras ferroviarias.
INFO:__main__:   ✅ Expected: ['Infrastructure', 'Hydraulics']
INFO:__main__:   🧩 Detected: ['Railway', 'Hydraulics', 'Railroad', 'Infrastructure']
INFO:__main__:   📊 Precision: 0.5, Recall: 1.0, F1: 0.67

INFO:__main__:🧠 [22] Testing query (en): We analyze rotating machines and piping systems in a power plant.
INFO:__main__:   ✅ Expected: ['Energy', 'Equipment and facilities', 'Rotating Machines', 'Piping']
INFO:__main__:   🧩 Detected: ['Fluid Mechanics', 'Equipment and facilities', 'Energy', 'Piping', 'Electro-mechanical Equipment', 'Rotating Machines']
INFO:__main__:   📊 Precision: 0.67, Recall: 1.0, F1: 0.8

INFO:__main__:🧠 [23] Testing query (fr): Étude sur la dissipation thermique et la dynamique des fluides.
INFO:__main__:   ✅ Expected: ['Energy', 'Fluid Mechanics', 'Thermal Dissipation', 'Fluid Dynamics']
INFO:__main__:   🧩 Detected: ['Energy', 'Fluid Mechanics', 'Thermal', 'Fluid Dynamics', 'Thermal Dissipation']
INFO:__main__:   📊 Precision: 0.8, Recall: 1.0, F1: 0.89

INFO:__main__:🧠 [24] Testing query (es): Proyecto relacionado con la mecánica de fluidos y electromagnetismo.
INFO:__main__:   ✅ Expected: ['Energy', 'Fluid Mechanics', 'Electromagnetism']
INFO:__main__:   🧩 Detected: ['Fluid Dynamics', 'Fluid Mechanics', 'Electromagnetism', 'CEM (Comptabilité électromagnétique)']
INFO:__main__:   📊 Precision: 0.5, Recall: 0.67, F1: 0.57

INFO:__main__:🧠 [25] Testing query (en): Installing Ethernet and radio communication for railway systems.
INFO:__main__:   ✅ Expected: ['Low Voltage', 'Radio / Wireless', 'Wired Transmissions']
INFO:__main__:   🧩 Detected: ['Ethernet 802.3', 'Radio / Wireless', 'EN50128', 'Low Voltage']
INFO:__main__:   📊 Precision: 0.5, Recall: 0.67, F1: 0.57

INFO:__main__:🧠 [26] Testing query (fr): Mise en place d’un système d’interphonie et de sonorisation dans les stations.
INFO:__main__:   ✅ Expected: ['Interphonie', 'Sonorisation']
INFO:__main__:   🧩 Detected: ['Low Voltage', 'Sonorisation', 'Radio / Wireless', 'Interphonie']
INFO:__main__:   📊 Precision: 0.5, Recall: 1.0, F1: 0.67

INFO:__main__:🧠 [27] Testing query (es): Configuramos routers y conmutadores Ethernet industriales.
INFO:__main__:   ✅ Expected: ['Routeurs et IAD', 'Commutateurs Ethernet']
INFO:__main__:   🧩 Detected: ['Routeurs et IAD', 'Commutateurs Ethernet']
INFO:__main__:   📊 Precision: 1.0, Recall: 1.0, F1: 1.0

INFO:__main__:🧠 [28] Testing query (en): Following LOI MOP and BIM standards for the construction project.
INFO:__main__:   ✅ Expected: ['LOI MOP', 'BIM']
INFO:__main__:   🧩 Detected: ['LOI MOP', 'BIM']
INFO:__main__:   📊 Precision: 1.0, Recall: 1.0, F1: 1.0

INFO:__main__:🧠 [29] Testing query (fr): Le projet est géré sous Ps Next et conforme à la norme Cenelec.
INFO:__main__:   ✅ Expected: ['Ps Next', 'Cenelec']
INFO:__main__:   🧩 Detected: ['Cenelec', 'Ps Next']
INFO:__main__:   📊 Precision: 1.0, Recall: 1.0, F1: 1.0

INFO:__main__:🧠 [30] Testing query (es): Usamos Capella y SysML para modelar la arquitectura del sistema.
INFO:__main__:   ✅ Expected: ['Capella', 'SYSml']
INFO:__main__:   🧩 Detected: ['SYSml', 'capella']
INFO:__main__:   📊 Precision: 1.0, Recall: 1.0, F1: 1.0

INFO:__main__:📈 SUMMARY REPORT
INFO:__main__:Average Precision: 0.71, Average Recall: 0.92, Average F1-score: 0.78
```
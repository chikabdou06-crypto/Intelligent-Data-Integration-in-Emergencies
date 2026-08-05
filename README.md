# Municipal Intelligence Agent

A highly capable, multi-modal, Retrieval-Augmented Generation (RAG) agent designed to interact with both local vaults of data and live public APIs. The agent acts as an emergency response, natural hazard, and telemetry analyst (specifically tailored for the Comunitat Valenciana region, but easily expandable).

## Features

- **Two-Phase Agentic Pipeline**: 
  - **Planner**: Deconstructs user prompts and determines exactly which tools (and how many) to use, automatically piping outputs from one tool into the inputs of the next.
  - **Synthesizer**: Synthesizes the raw data from the executed tools into a cohesive, highly specific response.
- **Multi-Provider Fallback Routing**: Uses `Gemini` as the primary reasoning and vision engine, automatically falling back to `Hugging Face` (Llama 3 / Qwen) or local `Ollama` instances if rate limits or network issues occur.
- **Multimodal Visual Analysis**: Can request live telemetry maps from external APIs, intercept the image bytes, and use Gemini 2.5/3.5 Vision models to "read" the map and answer specific user questions.
- **Live AEMET Telemetry**: Direct integrations with the Spanish Meteorological Agency (AEMET) OpenData REST API to fetch live lightning strike maps, UV indexes, fire risk forecasts, and mountain conditions.
- **Dynamic Local Vault**: Scans local `csv` and `pdf` directories to answer localized questions using the `vault_catalog` tool.
- **Cyberpunk Dashboard UI**: A fully responsive frontend UI featuring a chat terminal, live system clock, and a dedicated image viewer for rendering live API maps dynamically.

## Quickstart

### 1. Environment Setup
Rename `.env.example` to `.env` and fill in your API keys. At minimum, you will need:
- `GOOGLE_API_KEY` (For Gemini 2.5/3.5 Flash LLM and Vision models)
- `AEMET_API_KEY` (To pull live meteorological maps)

### 2. Install Dependencies
Ensure you have Python 3.10+ installed.
```bash
pip install -r requirements.txt
```

### 3. Run the Server
The FastAPI backend serves both the `/api/chat` endpoints AND the static frontend UI.

```bash
cd backend
python app.py
```

### 4. Access the Dashboard
Open your browser and navigate to:
```
http://localhost:8000
```

## Architecture

```text
├── backend/
│   ├── app.py                  # Main FastAPI server entrypoint
│   ├── core/                   # LLM providers, Planner, Orchestrator, Synthesizer
│   ├── tools/                  # The agent's capabilities
│   │   ├── api/                # Live API endpoints (AEMET, Vision Analyzer)
│   │   └── local/              # Vault and local filesystem tools
│   ├── vault/                  # The local knowledge base (CSVs, PDFs)
│   └── scratch/                # Debugging and testing scripts
├── frontend/                   # Vanilla JS/CSS Cyberpunk Dashboard
├── .env.example                # Template for required environment variables
└── README.md                   # This file
```

## Testing
Ad-hoc test scripts for LLM stress testing, AEMET API deep-dives, and tool execution can be found in `backend/scratch/`.

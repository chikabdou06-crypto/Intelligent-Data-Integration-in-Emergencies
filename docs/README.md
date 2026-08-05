 # Municipal Intelligence Agent

Welcome to the **Municipal Intelligence Agent**. This project is a highly advanced, fully modular, and LangChain-free Retrieval-Augmented Generation (RAG) platform. 

It orchestrates a fleet of specialized plugins (tools) dynamically to answer complex user queries by synthesizing data from databases, graph networks, public APIs, and unstructured document vaults.

## 🚀 Vision
The primary vision of this architecture is to build a robust **Enterprise AI Agent** capable of executing **multi-step reasoning chains (Compact Mode)** without relying on heavy abstractions like LangChain. By utilizing the raw official SDKs (e.g. `google-genai` and `pinecone`), we achieve:
1. **Total Transparency**: You see exactly what is sent to the LLM. No hidden magic.
2. **Speed & Efficiency**: No overhead from bloated third-party wrappers.
3. **Extreme Extensibility**: The `@register_tool` OOP decorator allows any developer to drop a new python file into `backend/tools/`, and the engine will instantly discover, parse, and utilize it in the reasoning loops.

## 🏗️ Architecture

The system is decoupled into logical modules for maximum maintainability:

```
RAG_BASIC_TEST_LANGCHAIN/
│
├── backend/
│   ├── app.py                   # FastAPI Application Entrypoint
│   ├── core/                    # Core Engine Logic
│   │   ├── base_tool.py         # Abstract OOP Template for Tools
│   │   ├── llm.py               # Raw Google GenAI SDK wrapper
│   │   ├── planner.py           # LLM Multi-step Planner
│   │   ├── orchestrator.py      # Execution Engine (handles $PREV chains)
│   │   ├── synthesis.py         # Final reasoning Synthesizer
│   │   └── registry.py          # Lazy-loaded tool registry
│   │
│   ├── tools/                   # Dynamic Plugin Ecosystem
│   │   ├── api/                 # Live Data Tools (AEMET Weather, Google Drive)
│   │   └── data/                # Data Tools (Neo4j, Pinecone RAG, CSV aggregations)
│   │
│   ├── clients/                 # Database Clients (Neo4j, Supabase)
│   ├── ingest/                  # Data Ingestion scripts (PDF -> Pinecone)
│   └── vault/                   # The Vault (Local Data & SQLite Cache - Git Ignored)
│
├── frontend/                    # Vanilla JS, HTML, CSS UI
├── scripts/                     # Developer Scripts (Generate Registry, Push to GitHub)
└── tests/                       # Unit Test Suite
```

## 🛠️ The Tool Ecosystem

The Agent operates by writing a dynamic plan in JSON (up to 4 steps) choosing from the following capabilities:
- **Neo4j Graph Expansion**: 4 generic tools (`neo4j_query`, `neo4j_schema`, `neo4j_create`, `neo4j_delete`) giving the agent full CRUD capability over the enterprise policy graph.
- **CSV Data Mining**: Server-side aggregation (`csv_aggregate`) allows the agent to compute vast datasets without row-caps.
- **Vault Pinecone RAG**: Semantic similarity lookups natively using `google-genai` embeddings and the raw Pinecone Python client.
- **Live APIS**: AEMET Weather and Google Drive integrations with robust offline fallback modes.

## 🔐 Security & Data Governance

- **Zero Data Uploads to GitHub**: The `backend/vault/` folder is strictly ignored. Only the engine is committed to GitHub.
- **Secure Credentials**: Credentials are managed via a local `.env` file (see `.env.example`).
- **Push Scripts**: Code deployments are handled securely via `push_to_github.ps1`, ensuring caching artifacts and sensitive logs never reach the public.

## ⚙️ Getting Started

### 1. Requirements
- Python 3.10+
- Set up a virtual environment (optional but recommended)

### 2. Installation
```bash
pip install -r pyproject.toml
# Or if using a modern tool like poetry or uv:
# uv pip install -e .
```

### 3. Setup Environments
Duplicate the `.env.example` file and rename it to `.env`. Fill in your API keys (Google, Pinecone, Neo4j).

### 4. Run the API Engine
```bash
python backend/app.py
```
This boots the FastAPI server which also serves the frontend UI. Navigate to the indicated localhost URL.

### 5. Running Tests
```bash
python tests/test_registry.py
python tests/test_tools.py
```

## 🧩 Modifying the Engine
To add a new tool:
1. Create a python file in `backend/tools/api/` or `backend/tools/data/`.
2. Inherit from `BaseTool`.
3. Add the `@register_tool` decorator.
4. Run `python backend/scripts/generate_lazy_registry.py`.

The Agent will immediately know how to use your new tool!

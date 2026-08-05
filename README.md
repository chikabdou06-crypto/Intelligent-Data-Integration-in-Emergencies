# Municipal Intelligence Agent 🏙️

Welcome to the **Municipal Intelligence Agent**. This project is a highly advanced, fully autonomous Retrieval-Augmented Generation (RAG) platform specialized in analyzing municipal demographics, economics, and environmental hazards for the Comunitat Valenciana and Spain.

Unlike traditional RAG systems that rely on vector databases alone, this agent dynamically selects and orchestrates multiple tools—live APIs, geospatial data sets, and local demographic CSVs—to answer complex queries spanning several domains.

---

## ✨ Capabilities

- **Autonomous Tool Orchestration:** An intelligent planner breaks down user queries into actionable steps, executing tools sequentially or in parallel without human intervention.
- **Dynamic Dataset Aggregation:** Capable of scanning, filtering, and aggregating thousands of rows across local demographic and economic CSVs in milliseconds.
- **Live Environmental & Civic APIs:** Direct integration with AEMET (Spanish State Meteorological Agency) for real-time weather, extreme risk warnings (fire/marine), and historical climatology, alongside civic data sources like the INE and BOE.
- **High-Availability Fallback Chain:** Automatically switches between LLM models (Gemini Flash, Gemini Flash Lite, Hugging Face, Ollama) if rate limits or availability issues occur, ensuring the server never hangs.
- **MCP Server Ready:** Exposes its tools via the Model Context Protocol (MCP), allowing standard AI clients (like Claude Desktop) to connect and utilize the municipal datasets directly.

---

## 📊 Datasets Included

The agent is pre-loaded with critical municipal and regional datasets located in `backend/vault/csvs`:

- `resultados_alquileres_final.csv`: Comprehensive rental market data.
- `riesgo_inundaciones.csv`: Flood risk assessments across municipalities.
- `Secciones_Censales.csv`: Geographic census tracts.
- `Sexo_y_nivel_estudios.csv` / `pais_nacimiento_y_nivel_estudios.csv`: Demographic breakdowns of education and birthplace.
- `Sexo_y_ocupacion_limpio.csv` / `Sexo_y_situacion_profesional_limpio.csv`: Employment, occupation, and professional status metrics.
- `paro_2008_2025.csv`: Historical unemployment data.

*(Note: Large raw datasets are safely kept in `.gitignore` to prevent GitHub storage limit errors, but the agent indexes and processes them locally.)*

---

## ⚠️ Limitations & Considerations

- **API Rate Limits:** The AEMET OpenData API has strict per-minute quota limits. If exceeded, the agent may temporarily fail to fetch live weather until the quota resets.
- **Token Windows:** While the agent can aggregate large CSVs, it automatically bounds queries to `max_rows=50` to prevent LLM context window overflows during synthesis.
- **Geographic Scope:** The datasets and APIs are heavily tuned for Spain (specifically the Comunitat Valenciana). Queries outside this region will primarily rely on the LLM's baseline knowledge rather than live RAG data.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A valid Google API Key (`GOOGLE_API_KEY`) for Gemini LLMs.
- A valid AEMET OpenData API Key (`AEMET_API_KEY`).

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/chikabdou06-crypto/municipal-intelligence-agent.git
   cd municipal-intelligence-agent
   ```

2. **Set up your environment variables:**
   Duplicate the `.env.example` file (or create a `.env` file) and add your keys:
   ```env
   GOOGLE_API_KEY=your_google_key
   AEMET_API_KEY=your_aemet_key
   ```

3. **Run the server:**
   The easiest way to start the FastAPI server with the built-in UI:
   ```bash
   python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
   ```
   *Then visit `http://127.0.0.1:8000` in your browser.*

---

## 🏗️ Architecture
- **Planner (`backend/core/planner.py`):** Translates user intent into a strict JSON array of tool calls.
- **Executor (`backend/core/orchestrator.py`):** Runs the tools securely.
- **Synthesizer (`backend/core/synthesis.py`):** Combines the raw tool outputs into a conversational, highly formatted markdown response.

*Designed for municipal open data integration.*

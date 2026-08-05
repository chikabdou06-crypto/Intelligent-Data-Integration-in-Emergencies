# RAG Emergency Assistant — Core Architecture Technical Report

---

## 1. Introduction

This document describes the internal architecture of the **RAG Emergency Assistant**, an autonomous, multi-step AI agent built to handle emergency response, natural hazard analysis, and regional telemetry for the **Comunitat Valenciana**. The system is not a simple chatbot — it is a modular pipeline that plans, executes, and synthesizes information from both local knowledge vaults and live public APIs in a single request cycle.

The agent is built entirely in **Python 3.10+** with **FastAPI** as the web server, and it uses a custom agentic architecture — no external agent framework like LangChain or LlamaIndex is used. Every component (the planner, the orchestrator, the synthesizer, the tool system, the cache) was designed from scratch to provide full control over the execution flow, making the system transparent, debuggable, and easy to extend.

The tech stack includes:

- **FastAPI** for the REST API entry point
- **Google Gemini** (primary LLM) with fallback to Hugging Face Inference API and Ollama
- **Pinecone** as the vector store for semantic PDF search
- **SQLite** as the execution cache
- **Google Drive API** for cloud document access
- **AEMET OpenData**, **SISCOVA**, **PATRICOVA**, and **ICV** as live data APIs

---

## 2. Vision

The vision for this project is to create an intelligent emergency response assistant capable of:

1. **Fusing multiple data sources in real time.** The agent can pull live weather warnings from AEMET, live earthquake data from SISCOVA, flood risk zones from PATRICOVA, and simultaneously query local CSV databases, PDF documents, and Google Drive files — all in a single request. The user asks one question and the system orchestrates multiple tools to build a comprehensive answer.

2. **Acting as an autonomous planner**, not just a retriever. Unlike basic RAG systems where a user query is embedded and matched against a vector store, this system uses an LLM to **plan** which tools to call, in what order, and with what arguments. It then executes the plan and synthesizes the results. This is known as **Agentic RAG** — the LLM decides what, when, and how to retrieve.

3. **Being extensible through a plug-in tool system.** Any new data source (a new API, a new CSV, a new database) can be added by simply writing a new Python class that extends `BaseTool` and registering it. The LLM automatically discovers the new tool on the next request.

4. **Regional specialization.** The system is specifically designed for the Comunitat Valenciana, with deep knowledge of PELSISCAV emergency protocols, local municipality codes, fire risk maps, seismic catalogs, and flood risk layers.

---

## 3. Overall General Structure

The system follows a strict **three-phase linear pipeline**:

```
User query (string)
        │
        ▼
┌──────────────────────────────────────┐
│  PHASE 1 — PLANNER  (planner.py)     │
│  Receives the user prompt.           │
│  Discovers relevant skills.          │
│  Builds the tool menu.              │
│  Calls the LLM to generate a JSON   │
│  execution plan (1 to 6 steps).      │
└──────────────────────────────────────┘
        │
        ▼  list of steps [{tool, arguments}, ...]
┌──────────────────────────────────────┐
│  PHASE 2 — ORCHESTRATOR              │
│  (orchestrator.py)                   │
│  Executes each step sequentially.    │
│  Resolves cross-step dependencies.   │
│  Checks the SQLite cache before      │
│  calling a tool.                     │
│  Stores results for the next phase.  │
└──────────────────────────────────────┘
        │
        ▼  list of executed steps with results
┌──────────────────────────────────────┐
│  PHASE 3 — SYNTHESIZER               │
│  (synthesis.py)                      │
│  Receives the original prompt plus   │
│  the entire execution trace.         │
│  Calls the LLM to produce a final   │
│  Markdown report.                    │
└──────────────────────────────────────┘
        │
        ▼  final markdown response → JSON to client
```

The entire cycle happens inside a single HTTP `POST /api/chat` request. The entry point in `app.py` wraps the synchronous pipeline in `run_in_threadpool()` so it doesn't block FastAPI's async event loop.

---

## 4. Data Sources — Types, Coverage & Limitations

The system can access data from five major categories: **Live APIs**, **Web Scrapers**, **Local CSVs**, **PDF Documents**, **Google Drive**, and **Databases**.

### 4.1 — Live API Tools

These tools call external REST APIs in real time. The data is always fresh but depends on API availability and rate limits.

| Tool | Source | Data Coverage | Fields / What You Can Look Up | Limitations |
|------|--------|---------------|-------------------------------|-------------|
| `aemet_forecast` | AEMET OpenData API | Daily weather forecast for any municipality in Spain (today + next 6 days) | Temperature (min/max), precipitation probability, wind speed/direction, sky conditions, UV index | Requires an AEMET API key. Uses a two-step request pattern (get metadata URL → get data URL). Municipality matching uses a fuzzy alias system. |
| `aemet_warnings` | AEMET OpenData CAP API | Active meteorological hazard warnings for the Comunitat Valenciana (area code 61) | Event type (rain, wind, heat, coastal), severity, urgency, certainty, color level (yellow/orange/red), onset time, expiry time, affected area names | Data arrives as a `.tar` archive containing CAP 1.2 XML files. Only Spanish-language entries are kept (to avoid duplicates). Not cacheable — must be queried live. |
| `aemet_fire_risk` | AEMET OpenData API | Fire risk level maps for the current day and day+1 (estimated/predicted) | Returns a PNG image URL of the fire risk map, plus metadata. Can be chained with `vision_map_analyzer` to "read" the image. | Returns an image, not structured data. Requires multimodal vision (Gemini) to interpret the map contents. |
| `aemet_lightning` | AEMET OpenData API | Real-time lightning map for the Iberian Peninsula | Returns a PNG image URL with lightning strike locations | Same as fire risk — image-based, needs vision to interpret. |
| `aemet_climatology` | AEMET OpenData API | Historical climatological data for a specific station and date range | Temperature, precipitation, humidity, wind values for past dates | Limited to stations in AEMET's network. Requires station ID (resolved from municipality name). |
| `aemet_observations` | AEMET OpenData API | Latest real-time observations from weather stations | Current temperature, humidity, wind, pressure, precipitation | Only returns data from stations with active sensors. |
| `aemet_marine` | AEMET OpenData API | Coastal weather forecast for Valencian coast zones | Wave height, wind speed, sea conditions, visibility | Coverage limited to defined coastal areas. |
| `aemet_mountain` | AEMET OpenData API | Mountain weather forecast for Valencian mountain areas | Snow level, wind chill, temperature at altitude, conditions | Coverage limited to defined mountain areas. |
| `siscova_earthquakes` | GVA Open Data WFS (SISCOVA) | Live feed of seismic events in the Comunitat Valenciana | Date, time (UTC), magnitude, depth (km), latitude, longitude, municipality, province, zone | Filters out future-dated test entries. Sorts newest-first. Limited by GVA server availability. The WFS endpoint returns CSV. |
| `patricova_flood_risk` | GVA ArcGIS REST API (PATRICOVA) | Official flood risk zone classification for any coordinate in the Comunitat Valenciana | Flood risk level (leyenda) for the queried point | Accepts lat/lon or a location name (auto-geocoded via Nominatim/OpenStreetMap). ArcGIS Identify endpoint with strict 1-point tolerance. |
| `icv_wms_search` | ICV WMS/WFS services | Geospatial data layers from the Institut Cartogràfic Valencià | Cadastral data, topographic features, land use | Limited to what ICV publishes on their WMS. |
| `web_search` | DuckDuckGo | General internet search — fallback when no specialized tool covers the query | Title, snippet, URL for top results | Capped at 5 results max. No login or JavaScript support. Uses the `duckduckgo-search` library. |
| `vision_map_analyzer` | Gemini Vision API | Reads and interprets satellite/weather map images | Spatial analysis text — what zones are affected, risk levels visible on the map | Only works with Gemini (multimodal). Not cacheable. Requires a valid image URL as input. |
| `general` | N/A (no-op) | Catch-all for conversational queries (greetings, clarifications) | N/A | Does nothing — just signals the Synthesizer to handle the query as free-form text. |

### 4.2 — Web Scrapers

| Tool | Source | What It Scrapes | Limitations |
|------|--------|-----------------|-------------|
| `siscova_scraper` | SISCOVA web page | Earthquake data from the SISCOVA portal via HTML scraping, as a fallback to the API | Fragile to HTML layout changes. Slower than the API. |

### 4.3 — Local CSV Files

CSV files live in `backend/vault/csvs/` and `backend/vault/processed_data/`. The system provides three tools for interacting with them:

| Tool | Purpose | Capabilities | Limitations |
|------|---------|-------------|-------------|
| `csv_list` | Lists all available CSV files | Returns filename + column names for every CSV in the vault | Discovery only — does not read data. |
| `csv_reader` | Reads and queries CSV data | Dual column filters (with operators: `contains`, `==`, `>`, `<`, `>=`, `<=`), sorting (`order_by` + `order_desc`), column exclusion, automatic geometry column stripping | Results capped at 500 rows (default). |
| `csv_aggregate` | Server-side aggregation | `sum`, `count`, `avg`, `min`, `max` with optional `group_by` — processes ALL rows, no cap | Cannot return individual rows — only aggregate values. |

**Key CSV files in the vault include:**

- `pelsiscav_clean_seismic_catalog.csv` — Historical earthquake catalog with magnitude, depth, epicenter, date, intensity
- Municipality code mappings, risk assessment tables, processed AEMET risk summaries

### 4.4 — PDF Documents (Semantic Search via Pinecone)

| Tool | Purpose | How It Works | Limitations |
|------|---------|-------------|-------------|
| `vault_pdf_search` | Semantic search over indexed PDF documents | Embeds the user query with Gemini `text-embedding-004` (768 dimensions), queries Pinecone vector store for top-k similar chunks | Depends on Pinecone and Gemini Embedding API availability. Chunks capped at 2000 chars each. Only searches pre-indexed PDFs. |

**Indexed PDFs include:** PELSISCAV emergency protocol manuals, risk assessment reports, regional planning documents.

### 4.5 — File Reader (Multi-format)

| Tool | Formats Supported | Capabilities |
|------|-------------------|-------------|
| `file_reader` | CSV, PDF, TXT, JSON, Markdown, Excel (XLSX) | Reads any file from the vault. For CSVs, delegates to `csv_reader`. For PDFs, extracts text with `pdfplumber`. For JSON, parses and returns structured data. Path-traversal protection prevents reading files outside the vault. |

### 4.6 — Google Drive Integration

| Tool | Purpose | How It Works | Limitations |
|------|---------|-------------|-------------|
| `drive_list` | Lists files in the authorized Google Drive folder | OAuth 2.0 via `token.json`. Lists files inside the sandboxed folder (`GOOGLE_DRIVE_FOLDER_ID`). | Only accesses one authorized folder. Requires OAuth token refresh. |
| `drive_read` | Reads a file from Google Drive | Downloads file content by filename or file ID. Supports text, CSV, and binary files. | Security: `is_file_authorized()` traces parent IDs up to 5 levels to verify the file is inside the sandbox. |
| `drive_read_sheet` | Reads a Google Sheet | Uses the Google Sheets API to read spreadsheet data natively (not as CSV download). Supports filtering, sorting, and column selection. | Only works with Google Sheets format, not uploaded Excel files. |

**Google Drive contains:** San Vicente del Raspeig municipal data — employment statistics, district (distritos) data, cadastral (catastro) records, budget files.

### 4.7 — Databases (Scaffolded but Not Active)

The `.env` template includes connection strings for:

- **Pinecone** — actively used for PDF vector search
- **Neo4j** — knowledge graph connector (scaffolded in `VaultCatalogTool` with a Cypher health check, but the graph is currently empty/disconnected)
- **Supabase** — PostgreSQL connector (environment variables defined but not actively used in any tool)

These are ready to be integrated. Adding a new database tool would just require a new `BaseTool` subclass.

### 4.8 — Self-Discovery Tools

| Tool | Purpose |
|------|---------|
| `vault_discover` | Scans the entire vault and returns a structured inventory of all available data: raw PDFs, indexed PDFs, CSVs, processed data, text files, and preprocessing scripts |
| `tool_discover` | Lists every registered tool with its full schema (name, description, parameters, required fields) |

---

## 5. The Core — Module-by-Module Deep Dive

The core lives in `backend/core/`. Here is every module, what it does, and how each important function works internally.

### 5.1 — `base_tool.py` — The Tool Contract

**What it is:** An abstract base class that every tool must extend.

**Why it exists:** It enforces a uniform interface so the Orchestrator can call any tool the same way: `tool.execute(**kwargs)`. It also provides automatic schema generation so the Planner knows what parameters each tool accepts.

**Class attributes:**

| Attribute | Type | Purpose |
|-----------|------|---------|
| `name` | str | Unique identifier — must match the key in the lazy registry |
| `description` | str | Shown to the Planner LLM so it knows what the tool does |
| `category` | str | Grouping: `DATA`, `API`, `ANALYSIS`, `DISCOVERY` |
| `cacheable` | bool | If `False`, the Orchestrator skips cache lookup and never stores results |

**Key function — `get_schema()`:**

This is a `@classmethod` that uses Python's `inspect.signature()` to read the type hints on the `execute()` method at runtime. It builds a JSON schema dynamically:

```python
@classmethod
def get_schema(cls):
    sig = inspect.signature(cls.execute)

    for name, param in sig.parameters.items():
        if name == "self": continue

        # Map Python types to JSON Schema types
        if   param.annotation == int:   param_type = "integer"
        elif param.annotation == bool:  param_type = "boolean"
        elif param.annotation == float: param_type = "number"
        elif param.annotation == list:  param_type = "array"
        else:                           param_type = "string"

        properties[name] = {"type": param_type}

        # If a parameter has no default value, it's required
        if param.default == inspect.Parameter.empty:
            required.append(name)
```

**Why this matters:** When you add a new tool with typed parameters like `def execute(self, city: str, radius: int = 10)`, the schema is automatically generated. The Planner sees it in the tool menu without any prompt editing.

---

### 5.2 — `registry.py` & `_lazy_registry_static.py` — The Lazy Registry

**What it is:** A mapping system that connects tool names to their Python classes — but only imports them when they're actually needed.

**Why it exists:** If we imported all 25+ tool modules at server startup, we'd load every dependency (requests, pdfplumber, pandas, Pinecone SDK, Google APIs, etc.) immediately. The lazy registry keeps startup fast — tools are imported on first use.

**How it works:**

The static map (`_lazy_registry_static.py`) is an auto-generated file:

```python
STATIC_TOOL_MAP = {
    "aemet_fire_risk":  ["backend.tools.api.aemet_fire_risk",  "AemetFireRiskTool"],
    "csv_reader":       ["backend.tools.local.csv_reader",     "CsvReaderTool"],
    "siscova_earthquakes": ["backend.tools.api.siscova_api",   "SiscovaEarthquakesTool"],
    # ... 22 more entries
}
```

**Key functions:**

- **`list_all_tools()`** — Returns all tool names from the static map instantly (no imports). Used by the Planner to build the tool menu.
- **`get_tool(tool_name)`** — The first time a tool is requested, it calls `importlib.import_module(module_path)` to load the module, then `getattr(module, class_name)` to get the class, and finally `ToolClass()` to instantiate it.
- **`@register_tool(name, category)`** — A decorator that sets name/category on a tool class at definition time.

---

### 5.3 — `catalog_loader.py` — Reading the Data Catalogs

**What it is:** A set of functions that read and write the JSON catalog files in `backend/vault/catalogs/`.

**Why it exists:** The catalogs are the indexes that tell the system what data exists in the vault. They are created by the ingestion pipeline (`backend/ingest.py`) and read by the Planner at every request.

**Functions:**

| Function | Reads | Returns |
|----------|-------|---------|
| `load_csvs_catalog()` | `csvs_index.json` | Dict mapping CSV filenames → column lists |
| `load_pdfs_catalog()` | `pdfs_index.json` | Dict with PDF summaries, chunk counts, Pinecone index name |
| `load_drive_catalog()` | `drive_catalog.json` | Dict with Google Drive file names and column schemas |
| `save_csvs_catalog(data)` | — | Writes updated CSV catalog (used during ingestion) |
| `save_pdfs_catalog(data)` | — | Writes updated PDF catalog (used during ingestion) |

Each function calls `ensure_vault_dirs()` first, which creates the vault directory structure if it doesn't exist yet. This makes the system self-initializing on first run.

---

### 5.4 — `vault_paths.py` — The File System Map

**What it is:** A single source of truth for all directory and file paths in the project.

**Why it exists:** Instead of constructing paths with `os.path.join()` scattered across the codebase, every path is defined once here and imported by other modules.

**Key constants:**

```python
VAULT_DIR           = backend/vault/
VAULT_PDFS          = backend/vault/pdfs/
VAULT_CSVS          = backend/vault/csvs/
VAULT_PROCESSED_DATA = backend/vault/processed_data/
CATALOGS_DIR        = backend/vault/catalogs/
PDFS_CATALOG_PATH   = backend/vault/catalogs/pdfs_index.json
CSVS_CATALOG_PATH   = backend/vault/catalogs/csvs_index.json
DRIVE_CATALOG_PATH  = backend/vault/catalogs/drive_catalog.json
```

**Key functions:**

- **`get_pinecone_index_name()`** — Reads the Pinecone index name from `PINECONE_INDEX_NAME` env var, defaults to `"tfm-vault"`
- **`get_pinecone_namespace()`** — Reads the namespace from `PINECONE_NAMESPACE` env var, defaults to `"vault-pdfs"`
- **`ensure_vault_dirs()`** — Creates all vault subdirectories if they don't exist (`os.makedirs(..., exist_ok=True)`)

---

### 5.5 — `llm.py` — The LLM Client

**What it is:** A multi-provider LLM client with automatic fallback and role-based model selection.

**Why it exists:** The system needs to work even when one provider is down. If Gemini is unavailable, it automatically falls back to Hugging Face. If that fails too, it falls back to a local Ollama instance.

**Provider priority:** Gemini → Hugging Face Inference → Ollama (local)

**Role-based model selection:** Different LLM roles use different model lists:

```python
ROLE_MODELS = {
    "planner":     { "gemini": ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-2.0-flash"], ... },
    "synthesizer": { "gemini": ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-2.0-flash"], ... },
    "general":     { "gemini": ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-2.0-flash"], ... },
}
```

**Key functions:**

- **`__init__(role, temperature)`** — Initializes all three providers with the model list for the given role. Skips providers that aren't configured (no API key).
- **`generate(prompt, image_bytes=None)`** — Sends a prompt to the LLM. Calls `_do_generate_with_fallback()` internally.
- **`_do_generate_with_fallback(prompt, image_bytes)`** — The retry loop. Tries each configured provider in order. If all fail, waits 1 second and retries up to 3 times. That's 3 providers × 3 retries = up to 9 attempts.
- **`generate_json(prompt, image_bytes)`** — Calls `generate()` then parses the response as JSON. The parsing logic:
  1. Strips `<thinking>...</thinking>` blocks (regex)
  2. Looks for JSON inside markdown fences (`` ```json ... ``` ``)
  3. If no fences, finds the first `{` or `[` character and the last matching `}` or `]`
  4. Calls `json.loads()` on the extracted text

---

### 5.6 — `network_patch.py` — DNS Bypass

**What it is:** A monkey-patch for Python's `socket.getaddrinfo()` that replaces the DNS resolution for `router.huggingface.co` with a hardcoded IP address.

**Why it exists:** Some restrictive networks (university, corporate) block DNS resolution for certain domains. This patch bypasses the block by resolving the hostname directly to an AWS IP (`18.172.213.11`).

```python
def _patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host == 'router.huggingface.co':
        host = '18.172.213.11'    # Known AWS IP
    return _orig_getaddrinfo(host, port, family, type, proto, flags)
```

Called at startup via `apply_network_patches()`.

---

### 5.7 — `planner.py` — The Brain (Phase 1)

**What it is:** The most complex module in the system. It transforms a user's raw text question into a structured JSON execution plan.

**Why it exists:** This is what makes the system "agentic" — instead of just embedding the query and searching a vector store (basic RAG), the Planner uses an LLM to reason about which tools to call, in what order, and with what arguments.

#### Function: `generate_plan(prompt)`

**What it does:** Takes a user prompt string, returns a `list[dict]` where each dict has a `"tool"` name and `"arguments"` dict.

**Internal steps:**

**Step 1 — Skill Discovery** (no LLM call):

```python
all_skills = discover_skills()    # reads backend/skills/*.md
selected = select_relevant_skills(prompt, all_skills)    # keyword match
```

Scans skill files, reads only YAML frontmatter. If any skill's description keywords match the user prompt, the full body of that skill is injected into the LLM context.

**Step 2 — Tool Menu Construction:**

```python
for tool_name in list_all_tools():
    tool = get_tool(tool_name)          # lazy import
    schema = tool.get_schema()          # introspect execute() parameters
    # formats into: - "csv_reader": Reads CSV files. Args: {filename: <str required>, ...}
```

**Step 3 — Vault Catalog Injection:**

```python
catalog_tool = VaultCatalogTool()
catalog = catalog_tool.execute()    # scans vault, Drive, PDFs
catalog_str = json.dumps(catalog, indent=2)
```

This is critical — the Planner literally runs the catalog tool before the LLM call so the model knows what files and data sources exist.

**Step 4 — LLM Call:**

```python
system_prompt = get_planner_prompt(catalog_str, skills_section, tools_text)
llm = LLMClient(role="planner", temperature=0.1)
result = llm.generate_json(system_prompt + f'\n\nUser Prompt: "{prompt}"')
```

Temperature 0.1 = very deterministic. The LLM returns a JSON plan.

**Step 5 — Plan Extraction:**

```python
steps = result.get("steps", [])
if not steps:
    steps = [{"tool": "general", "arguments": {}}]    # fallback
return steps[:6]    # hard cap at 6 steps
```

#### Function: `discover_skills()`

Scans `backend/skills/` for `.md` files. For each file, reads the YAML frontmatter (name + description) and the body (full Markdown instructions). Returns a list of skill dicts.

#### Function: `_parse_skill_frontmatter(raw)`

A lightweight YAML parser (does NOT use the `yaml` library). Finds text between `---` delimiters, extracts `name:` and `description:` lines by string prefix matching.

#### Function: `select_relevant_skills(prompt, all_skills)`

Tokenizes each skill's description into words > 3 characters. Checks if ANY of those words appear as substrings in the user's prompt. This is O(n·k) string matching — fast but imprecise. No embeddings, no LLM call.

---

### 5.8 — `orchestrator.py` — The Executor (Phase 2)

**What it is:** A deterministic execution engine. It takes the plan from the Planner and executes each step in sequence. It does NOT make any LLM calls.

**Why it exists:** It decouples reasoning (the Planner's job) from execution (the Orchestrator's job). This makes the execution layer predictable, testable, and fast.

#### Function: `execute_plan(steps)`

The main loop:

```python
executed = []
for step in steps:
    tool_name = step["tool"]
    args = step["arguments"]

    # 1. Resolve $PREV and $STEP_N placeholders
    resolved_args = _enrich_args_from_prior(args, executed)

    # 2. Skip "general" (no-op)
    if tool_name == "general":
        executed.append({"tool": tool_name, "result": None})
        continue

    # 3. Instantiate tool
    tool_instance = get_tool(tool_name)

    # 4. Check cache (if tool is cacheable)
    if tool_instance.cacheable:
        cached = get_cached_result(tool_name, resolved_args)
        if cached is not None:
            executed.append({..., "result": cached, "cached": True})
            continue

    # 5. Execute
    result = tool_instance.execute(**resolved_args)

    # 6. Cache if successful
    if result.get("status") != "error":
        set_cached_result(tool_name, resolved_args, result)

    executed.append({"tool": tool_name, "arguments": resolved_args, "result": result})
```

#### Function: `_resolve_placeholder(value, prior)`

Handles two placeholder syntaxes:

- **`$PREV.path.to.field`** — Searches backwards through ALL prior steps (most recent first) for a result that contains the given path. This handles cases where the immediately previous step might have failed.
- **`$STEP_N.path.to.field`** — Directly references step N (0-based index) in the executed list.

Both use `_deep_get()` for path navigation.

#### Function: `_deep_get(obj, path)`

A generic navigator for nested Python data structures. Splits the path by `.` and traverses dicts and lists:

```python
for part in path.split("."):
    if isinstance(obj, list):
        obj = obj[int(part)]     # numeric array index
    elif isinstance(obj, dict):
        obj = obj.get(part)      # dict key lookup
```

Example: `_deep_get({"data": [{"city": "Valencia"}]}, "data.0.city")` → `"Valencia"`

#### Function: `_enrich_args_from_prior(arguments, prior)`

Iterates every key-value pair in the step's arguments. If a value starts with `$`, calls `_resolve_placeholder()`. Otherwise leaves it untouched. Resolved values are cast to `str` to prevent type errors in tool execution.

---

### 5.9 — `prompts.py` — The System Prompts

**What it is:** Contains the two f-string templates that define the agent's behavior.

#### Function: `get_planner_prompt(catalog_str, skills_section, tools_text)`

Builds the Planner system prompt by injecting three dynamic blocks:

1. **Vault Catalog** — the JSON blob of available data sources
2. **Skills Section** — matched skill bodies (Markdown instructions)
3. **Tools Text** — one-line schema for each tool

The prompt enforces 6 mandatory rules:

1. **Cross-step dependencies:** `$PREV.path` syntax, no bracket notation
2. **Sorting:** Use `csv_reader` with `order_by` for max/min, not `csv_aggregate`
3. **Step limit:** Max 6 steps
4. **Chain of Thought:** Must write a `<thinking>` block before JSON
5. **Chitchat:** Greetings → single `general` step
6. **Output format:** JSON in markdown code block

And domain specializations:
- Seismic: historical → `csv_reader` on `pelsiscav_clean_seismic_catalog.csv`, live → `siscova_earthquakes` API
- Google Drive: look up filenames in catalog, pass as string (no `$PREV`)

#### Function: `get_synthesis_prompt(current_date, prompt, executed_plan_json)`

Builds the Synthesizer prompt. Injects the current timestamp, the original user question, and the full execution trace. Instructs the LLM to:

1. Cross-reference all data sources
2. Identify relationships and validation rules
3. Resolve discrepancies between sources
4. Present a professional Markdown report

---

### 5.10 — `synthesis.py` — The Narrator (Phase 3)

**What it is:** The final stage that produces the human-readable response.

#### Function: `generate_synthesis(prompt, executed_plan)`

```python
def generate_synthesis(prompt, executed_plan):
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    executed_plan_json = json.dumps(executed_plan, indent=2)

    synthesis_prompt = get_synthesis_prompt(current_date, prompt, executed_plan_json)

    llm = LLMClient(role="synthesizer", temperature=0.3)
    reply = llm.generate(synthesis_prompt).strip()

    # Remove <thinking> blocks
    reply = re.sub(r'<thinking>.*?</thinking>\s*', '', reply, flags=re.DOTALL)
    return reply.strip()
```

**Key points:**
- The entire execution trace (every tool call, every argument, every result) is serialized as JSON and injected into the prompt. The Synthesizer sees everything.
- `temperature=0.3` — slightly higher than the Planner for more natural prose, but still low enough to avoid hallucination.
- Current date is injected so the model correctly interprets temporal data.
- `<thinking>` blocks are stripped from the final output.

---

### 5.11 — `cache.py` — The Execution Cache

**What it is:** An SQLite-based cache that stores tool results, keyed by a SHA-256 hash of `tool_name + arguments`.

**Database schema:**

```sql
CREATE TABLE tool_cache (
    hash_key   TEXT PRIMARY KEY,
    tool_name  TEXT,
    result     TEXT,           -- JSON-serialized
    timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Key functions:**

- **`_generate_hash(tool_name, kwargs)`** — `SHA-256(tool_name + "::" + json.dumps(kwargs, sort_keys=True))`. The `sort_keys=True` ensures determinism regardless of argument order.
- **`get_cached_result(tool_name, kwargs)`** — Looks up the hash in SQLite. Returns the deserialized JSON result or `None`.
- **`set_cached_result(tool_name, kwargs, result)`** — Writes to SQLite with `INSERT OR REPLACE`. Error results are never cached.
- **`init_db()`** — Creates the table on module import if it doesn't exist.

**Caching rules:**
- Tools set `cacheable = False` to opt out (used by live tools: `aemet_fire_risk`, `aemet_warnings`, `vision_map_analyzer`)
- Error results (`status == "error"`) are never cached
- There is **no TTL** — cached results live forever until the database is cleared manually

---

## 6. Complete Core Function Reference

| Module | Function | What It Does |
|--------|----------|--------------|
| `planner.py` | `generate_plan(prompt)` | Assembles the full LLM prompt (skills + tools + catalog), calls LLM, returns JSON plan |
| `planner.py` | `discover_skills()` | Scans `backend/skills/*.md`, reads YAML frontmatter, returns skill metadata list |
| `planner.py` | `select_relevant_skills(prompt, skills)` | Keyword-matches user prompt against skill descriptions |
| `planner.py` | `_parse_skill_frontmatter(raw)` | Lightweight YAML parser for skill file headers |
| `orchestrator.py` | `execute_plan(steps)` | Main execution loop — resolve deps, check cache, execute tools |
| `orchestrator.py` | `_resolve_placeholder(value, prior)` | Resolves `$PREV.path` and `$STEP_N.path` from prior results |
| `orchestrator.py` | `_deep_get(obj, path)` | Navigates nested dicts/lists via dot-path strings |
| `orchestrator.py` | `_enrich_args_from_prior(args, prior)` | Substitutes all `$`-prefixed argument values |
| `synthesis.py` | `generate_synthesis(prompt, plan)` | Builds synthesis prompt, calls LLM, strips thinking blocks |
| `prompts.py` | `get_planner_prompt(...)` | Returns the Planner system prompt with dynamic injections |
| `prompts.py` | `get_synthesis_prompt(...)` | Returns the Synthesizer system prompt with execution trace |
| `base_tool.py` | `BaseTool.execute(**kwargs)` | Abstract — tool implementation entry point |
| `base_tool.py` | `BaseTool.get_schema()` | Introspects `execute()` type hints → JSON schema |
| `registry.py` | `list_all_tools()` | Returns tool names from static map (instant, no imports) |
| `registry.py` | `get_tool(name)` | Lazy-imports module, instantiates tool, returns instance |
| `cache.py` | `_generate_hash(name, kwargs)` | SHA-256 of tool name + sorted JSON args |
| `cache.py` | `get_cached_result(name, kwargs)` | SQLite lookup → deserialized result or None |
| `cache.py` | `set_cached_result(name, kwargs, result)` | SQLite INSERT OR REPLACE |
| `vault_paths.py` | `ensure_vault_dirs()` | Creates vault directory structure if missing |
| `vault_paths.py` | `get_pinecone_index_name()` | Returns Pinecone index name from env |
| `catalog_loader.py` | `load_csvs_catalog()` | Reads `csvs_index.json` |
| `catalog_loader.py` | `load_pdfs_catalog()` | Reads `pdfs_index.json` |
| `catalog_loader.py` | `load_drive_catalog()` | Reads `drive_catalog.json` |
| `network_patch.py` | `apply_network_patches()` | Monkey-patches DNS for Hugging Face |
| `llm.py` | `LLMClient.generate(prompt)` | Sends prompt to LLM with provider fallback |
| `llm.py` | `LLMClient.generate_json(prompt)` | Generates + parses JSON (strips thinking, finds fences) |

---

*RAG Emergency Assistant · Core Architecture Technical Report · July 2026*

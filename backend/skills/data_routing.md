---
name: data-routing
description: Universal multi-source routing and catalog-first data analysis. Teaches the agent to first query the vault catalog to discover all available local CSVs, text documents, PDF resumes, Neo4j nodes, and sandboxed Google Drive files before selecting tools, and details how to chain them seamlessly across sources.
---

# Universal Data Routing & Catalog-First Analysis

End-to-end workflow for answering questions that span multiple different data sources (local CSVs, local PDFs, Neo4j Knowledge Graph, live AEMET weather APIs, and Google Drive files).

---

## When to Use This Skill

**Activation Triggers**:
- Any prompt mentioning files, documents, sheets, spreadsheets, or folders.
- Any complex analytical question where the correct data source (local vs cloud vs graph) is not explicitly named.
- When cross-referencing between different *kinds* of data (e.g., matching a Google Drive document with a local CSV, or looking up weather API data then querying a spreadsheet).
- Any general informational query that might reside in the vault.

---

## Core Flow: Plan, Route, and Chain

The agent must always execute the following sequential phases:

### Phase 1: Review the Catalog
Before fetching any specific file or querying any database, **always review the VAULT CATALOG** provided at the top of your system prompt.
- **Why**: You cannot guess filenames or assume database connections are online. The VAULT CATALOG contains the exact schemas of all local CSVs, text/PDF files, Neo4j labels, and sandboxed Google Drive files. You DO NOT need to run a tool to get this, just read the prompt!

### Phase 2: Route and Select
Based on the results of `vault_catalog`, select the best tool(s) for the query using this routing matrix:

| Data Type | Best Primary Tool | Fallback Tool |
|-----------|-------------------|---------------|
| Tabular Data (Local CSV) | `csv_reader` (row-based) / `csv_aggregate` (for large sums/averages) | `file_reader` |
| Tabular Data (Excel .xlsx) | `file_reader` (using `sheet_name` and structured rows) | N/A |
| Plain Text / JSON / MD (Local) | `file_reader` (literal read) | N/A |
| PDF Documents (Semantic Search) | `vault_pdf_search` (Pinecone semantic search) | `file_reader` (literal extraction) |
| Neo4j Graph Data | `neo4j_query` (Cypher read-only queries after running `neo4j_schema`) | N/A |
| Google Drive Files (General) | `drive_read` (downloads to memory) | `drive_list` (discovery) |
| Google Drive Sheets | `drive_read_sheet` (structured rows) | `drive_read` (CSV export) |
| Real-time Meteorological Data | `aemet_forecast` / `aemet_warnings` | `general` |
| Getting Coordinates (Lat/Lon) | `general` (Ask: "What is the latitude and longitude of [City]?") | N/A |

**CRITICAL RULES:**
1. If you need to use `patricova_flood_risk`, you can pass the `location_name` parameter with the city name instead of using lat/lon. 
2. For seismic historical searches in `pelsiscav_clean_seismic_catalog.csv`, you MUST filter using `Localizacion` (not `Provincia`).
3. **No Extracted Coordinate Filtering in CSVs**: Never attempt to filter `riesgo_inundaciones.csv` or other CSVs using extracted coordinate bounds (like `lat_min`, `lat_max`). Use exact `municipio` or `Localizacion` names.
4. **Google Drive Sorting/Filtering**: When accessing Google Drive CSVs via `drive_read_sheet`, use its built-in `order_by`, `order_desc`, and `filter_column` parameters. **NEVER chain `drive_read_sheet` into `csv_reader`**.
5. **Anti-Hallucination for Column Names**: NEVER hallucinate column names for `order_by` or `filter_column`. If you do not know the exact column names, you MUST use two steps: Step 1: `drive_read_sheet` with `max_rows=1` to inspect the headers. Step 2: `drive_read_sheet` with the actual exact column name for sorting/filtering.
6. **Direct Data Fetching (No Discovery-Only Plans)**: NEVER create a plan that only calls discovery tools (`drive_list`, `csv_list`, `vault_discover`, `ine_search_operations`). If the user asks for unemployment, employment, social support, or income data, you MUST directly include a step that calls `drive_read_sheet(filename="demandantes_2008_2025.csv")`, `drive_read_sheet(filename="afiliados_2022_2025.csv")`, or `drive_read_sheet(filename="distribucion_por_fuente_de_ingresos.csv")`. Do not just list files!

### Phase 3: Pull Data
Execute the tool call. For tabular sources (CSV, Excel, Google Sheets), use `filter_column` and `filter_value` to reduce token size and filter rows server-side.

**Google Drive Subfolder Navigation**:
If the user asks for files, spreadsheets, or data regarding **San Vicente** (such as `Parcela_urbana.csv`, `ayuntamientos_alicante.csv`, `contratos_2006_2025.csv`, `paro_2008_2025.csv`, etc.), these files reside in the Google Drive folder named `TFMCSV_SANTVicente` (ID: `13jwbFGIGnEfzfKZxxjAv-hJrVDhml8qs`) located inside the `FOR_TEST_RAG` sandbox (ID: `1YIAqmtHkRjqDAu2KESGPeL6XV38Zu3hx`).
1. Check the VAULT CATALOG in your prompt to discover these cloud files.
2. Retrieve sheet contents using `drive_read_sheet` with the corresponding spreadsheet/file `id` (and optionally `sheet_name`).
3. For regular CSV files on Drive, you can download them using `drive_read` or read them using `drive_read_sheet` if they are spreadsheets.

### Phase 4: Chain and Cross-Reference
If the query requires connecting multiple sources (e.g., getting a list of municipalities from Google Drive and matching them with local unemployment CSV records):
1. **Fetch from Source A** in Step N.
2. **Inject into Source B** in Step N+1 using `$PREV` or `$STEP_X` dot-notation.
   - Example:
     - **Step 1**: `drive_read_sheet` (reads spreadsheet from Drive, returns list of dicts)
     - **Step 2**: `csv_aggregate` (filename="paro_2008_2025.csv", filter_column="Municipio", filter_value="$PREV.data.0.nombre", aggregate_columns="total Paro Registrado")
     - **Step 3**: `synthesis` (compiles final output)

---

## Chaining Syntaxes

- **`$PREV.path.to.field`**: Accesses the output of the immediate prior step.
  - E.g., `$PREV.data.0.id` or `$PREV.files.0.name`
- **`$STEP_X.path.to.field`**: Accesses the output of a specific historical step (where X is 0-indexed).
  - E.g., `$STEP_1.data.0.email`
- **Never use brackets `[]` for arrays in injection strings**. Use dot indexation (e.g. `data.0.name` instead of `data[0].name`).

# Agent Capabilities & Rollercoaster Testing Documentation

This document outlines the advanced capabilities, routing logic, and stress-testing results for the Multi-Tool RAG Agent developed for this TFM.

## 1. Google Drive "Raw CSV" Bypass Architecture
The agent is capable of interfacing with Google Drive repositories securely using OAuth or Public API keys. However, an architectural challenge arose where standard CSV files (`text/csv`) hosted on Google Drive were triggering `SERVICE_DISABLED` errors because the system attempted to read them via the Google Sheets API.

**The Solution:**
The `drive_read_sheet` tool was internally rewritten to intercept the file's `mimeType` using the Drive API before selecting an extraction method.
- If the file is `application/vnd.google-apps.spreadsheet`, it routes through the Google Sheets API.
- If the file is `text/csv` or `text/plain`, it **bypasses the Sheets API completely**. Instead, it downloads the raw text into memory via the Drive API, parses it using Python's native `csv.reader`, and pipes the data into the exact same filtering, ordering, and row-limiting logic as a standard sheet.
- **Result:** The agent can seamlessly read rows and columns from raw CSV files on Google Drive without requiring the user to enable the Google Sheets API on their Cloud Console.

## 2. Dynamic Google Drive Indexing
To prevent the user from having to explicitly mention the "Google Drive folder" in their prompts, a dynamic indexing script (`backend/ingest/index_drive.py`) was integrated into the `index_all.py` pipeline.
- This script scans the sandboxed `TFMCSV_SANTVicente` Google Drive folder.
- It caches the `file_id`, `filename`, and `mimeType` of all 73+ documents into a local `drive_catalog.json` file.
- The `vault_catalog` tool reads this JSON file instantly. 
- **Result:** When the LLM Planner runs `vault_catalog` as Step 0, it instantly knows the exact names and IDs of every file in the cloud, allowing it to autonomously route queries to `drive_read_sheet` without human hints.

## 3. Rollercoaster Stress Testing
To validate that the agent is "production-ready," two highly complex "rollercoaster" prompts were executed to test its multi-source routing capabilities.

### Test 1: The Multi-Hazard Municipal Profile
**Prompt:** *"I need to analyze the risk in San Vicente del Raspeig. First, find out what the population by gender is. Then, look up the flood hazard mapping data for the same municipality. Finally, check the historical seismic catalog to see if there have been any earthquakes greater than magnitude 2.0 in the ALACANT province. Summarize the combined risk profile."*

**Execution Path:**
1. `vault_catalog` (Discovers local CSVs, PATRICOVA PDFs, and Google Drive files).
2. `csv_reader` -> Target: `poblacion_segun_sexo.csv` (Demographics).
3. `vault_pdf_search` -> Target: PATRICOVA semantic search (Flood Hazard).
4. `csv_reader` -> Target: `pelsiscav_clean_seismic_catalog.csv` (Seismic Activity).
5. `synthesis` -> Synthesizes a master risk profile.

**Outcome:** The agent successfully parsed a single conversational sentence, broke it into four independent programmatic tool calls spanning local text, vector search, and cloud databases, and synthesized a professional multi-hazard report.

### Test 2: Live Weather vs Static Risk
**Prompt:** *"Cross-reference the current AEMET daily weather forecast for 'San Vicente del Raspeig' with the 'riesgo_inundaciones.csv' (flood risk) file to tell me if the current weather forecast exacerbates any known flood risks for that municipality."*

**Execution Path:**
1. `vault_catalog` (Discovers files).
2. `aemet_forecast` (Fetches live precipitation and wind data).
3. `drive_read_sheet` -> Target: `riesgo_inundaciones.csv` (Fetches spatial vulnerability).
4. `synthesis` -> Validates the live weather against the static trigger thresholds.

**Outcome:** The agent acted as a true real-time early warning system, successfully validating that the current 0mm precipitation forecast posed no immediate threat to the historically vulnerable urban drainage bottlenecks identified in the Drive CSV.

## 4. Resilience & Timeout Handling
To handle occasional `503 UNAVAILABLE` spikes (High Demand) from the Google Gemini API, the core LLM wrapper (`backend/core/llm.py`) implements a robust exponential backoff using the `tenacity` library.
- **Max Retries:** 5 attempts.
- **Wait Time:** Exponential scaling up to 30 seconds per retry.
- **Result:** The agent will gracefully pause and wait out server-side congestion rather than failing a complex plan mid-execution.

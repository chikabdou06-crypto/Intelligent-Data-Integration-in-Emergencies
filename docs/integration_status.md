# 📊 Data Integration Status Report

> Cross-references every dataset from [data_sources_report.md](./data_sources_report.md) against what is actually built and working in the codebase.
>
> Last updated: 2026-06-11
>
> ⚠️ **Cleanup performed**: ~300 non-emergency CSVs deleted (~1.5 GB freed). Focus: emergency data only.

---

## Quick Summary

| Status | Count | Meaning |
|--------|-------|---------|
| ✅ Integrated | 13 | Live tool or data in vault, fully queryable |
| 🟡 Partially Integrated | 0 | — |
| 🟠 Not Integrated | 3 | Needs endpoint research before building |
| ❌ Not Automatable | 3 | Institutional access or unknown format |

---

## ✅ Fully Integrated (7/19)

| Dataset ID | Method | Tool / File | How It Works |
|------------|--------|-------------|-------------|
| `spaicv31_siscova_sismos` | **Live WFS API** | [`siscova_earthquakes`](../backend/tools/api/siscova_api.py) | Calls GVA WFS endpoint → returns structured CSV of all seismic events since 2022. No API key needed. |





| `siscova-stations` | **Web Scraping** | [`siscova_scraper`](../backend/tools/api/siscova_scraper.py) | Scrapes the HTML table at `siscova.es/es/estaciones-sismicas` → returns station codes, coordinates, sensor types. 



| `spa_icv_orde_patricova` | **Live ArcGIS REST API** | [`patricova_flood_risk`](../backend/tools/api/patricova_flood.py) | Queries `carto.icv.gva.es` ArcGIS Identify endpoint with lat/lon → returns PATRICOVA flood risk level for that point. |




| `spa_icv_orde_patricova` | **Static CSV** | `peligrosidad_inun.csv` (9.2 MB) + `riesgo_inundaciones.csv` (6 MB) in [`vault/csvs/`](../backend/vault/csvs/) | Full flood hazard/risk GIS data downloaded as flat CSVs. Queryable via `csv_reader` and `csv_aggregate`. |



| `pelsiscav_anexo_b/e` | **PDF → Table Extraction** | ~210 `pelsiscav_table_*.csv` files in [`vault/csvs/`](../backend/vault/csvs/) | Tables extracted from the 45 MB PELSISCAV Annex PDF. Historical seismic catalog (1048–2009) + intensity tables. |




| `risk-cv` | **PDF → Table Extraction** | 14 `RESUM_RISCS_CV_*.csv` files in [`vault/processed_data/`](../backend/vault/processed_data/) | Municipal risk levels (floods, seismic, wildfires, snow, hazmat) extracted from `RESUM RISCS CV.pdf` via `pdf_to_tables.py`. |




| `aemet-warnings` | **Live REST API** | [`aemet_warnings`](../backend/tools/api/aemet_warnings.py) | Fetches CAP 1.2 XML hazard alerts from AEMET OpenData API for the Valencian Community. Requires `AEMET_API_KEY`. |
| `aemet-forecast-weather` | **Live REST API** | [`aemet_forecast`](../backend/tools/api/aemet_forecast.py) | Municipal weather forecast (daily 7-day + hourly 48h). Temperature, rain probability, wind, sky state. Default: San Vicente del Raspeig. |
| `aemet-forecast-marine` | **Live REST API** | [`aemet_marine`](../backend/tools/api/aemet_marine.py) | Coastal and high-sea marine predictions. Wave height, wind, swell, visibility. Default: Valencia & Murcia coast (code 46). |
| `aemet-forecast` (fire/UV) | **Live REST API** | [`aemet_fire_risk`](../backend/tools/api/aemet_fire_risk.py) | Wildfire risk maps (estimated + forecast) and UV radiation index (UVI) predictions up to 4 days ahead. |
| `aemet-opendata` (historical) | **Live REST API** | [`aemet_historical`](../backend/tools/api/aemet_historical.py) | Real-time station observations (last 12h) and historical daily climate data with date ranges. |





### Supporting integrations (not in the 19 datasets but working):

| Source | Method | Tool / File |
|--------|--------|-------------|
| Google Drive | OAuth 2.0 | [`drive_list`](../backend/tools/api/google_drive.py), `drive_read`, `drive_read_sheet` — read files from authorized Drive folder |
| Neo4j | Bolt protocol | [`neo4j_query`](../backend/tools/graph/neo4j_tools.py), `neo4j_schema`, `neo4j_create`, `neo4j_delete` — full graph CRUD |
| Pinecone | Vector DB | [`vault_pdf_search`](../backend/tools/local/vault_pdf_search.py) — semantic search over indexed PDFs/TXT |
| Local CSVs | File system | [`csv_reader`](../backend/tools/local/csv_reader.py), `csv_aggregate`, `csv_list` — 370+ CSV files queryable |
| Local files | File system | [`file_reader`](../backend/tools/local/file_reader.py) — reads CSV, PDF, TXT, JSON, XLSX from vault |
| Vault discovery | File system | [`vault_discover`](../backend/tools/discovery/discovery_tools.py), `tool_discover` — agent self-introspection |

---

## 🟡 Partially Integrated — NONE (All AEMET tools now built!)

> ✅ All 4 missing AEMET tools were built on 2026-06-11. They all use the same `AEMET_API_KEY` from `.env`.
> All follow the same 2-step pattern: (1) request → get `datos` URL, (2) fetch actual data from that URL.

---

## 🟠 Not Yet Integrated — Needs Research (5/19)

| Dataset ID | Provider | What's Blocking | Research Needed |
|------------|----------|-----------------|-----------------|
| `snczi-varios` | MITECO | Unknown if OGC endpoints are open | Check `sig.miteco.gob.es/snczi/` for WMS/WFS GetCapabilities |
| `chj-opendata` | Conf. Hidrográfica del Júcar | SAIH sensor API not verified | Explore `http://saih.chj.es/` for REST/WFS endpoints |
| `chs-opendata` | Conf. Hidrográfica del Segura | SAIH sensor API not verified | Explore CHS SAIH portal for similar endpoints |
| `ign-stations` | IGN | Download/API not confirmed | Check `www.ign.es` for seismic catalog download or API |
| `aemet-weather-atlas` | AEMET | May be under existing AEMET OpenData | Check if `/valores/climatologicos/normales/` covers this |

---

## ❌ Not Automatable (3/19)

| Dataset ID | Provider | Why | Workaround |
|------------|----------|-----|------------|
| `afon-alicante` | Univ. Alicante | Institutional access only — requires direct contact with the university's Seismic Unit | If they share data, drop CSV into `vault/csvs/` |
| `adaptecca-rcp-4.5-8.5` | AdapteCCa | Web viewer only, download format unknown (likely NetCDF) | Manual download → convert to CSV → drop in vault |
| `pnacc-ar6` | AEMET | Web viewer only, download format unknown | Same as above |

---

## 🔧 Infrastructure Status

| Component | Status | Notes |
|-----------|--------|-------|
| `.env` API Keys | ✅ | `GOOGLE_API_KEY`, `AEMET_API_KEY`, `PINECONE_API_KEY`, `NEO4J_*` configured |
| Pinecone Vector DB | ✅ | Index `tfm-vault`, namespace `vault-pdfs`, 6 files indexed |
| Neo4j Graph DB | ⚠️ | Tools ready, needs active Neo4j instance |
| Google Drive OAuth | ✅ | `credentials.json` + `token.json` present |
| Preprocessing Pipeline | ✅ | `backend/preprocessing/pdf_to_tables.py` working |
| CSV Ingestion | ✅ | 370+ files indexed across `vault/csvs/`, `vault/processed_data/`, `backend/data/` |

---

## Next Priority Actions

1. **🔴 Build `aemet_forecast` tool** — municipal weather (same API key, high value for risk assessment)
2. **🟡 Build `aemet_marine` tool** — coastal conditions
3. **🟡 Build `aemet_fire_risk` tool** — wildfire probability
4. **🟠 Research SNCZI/CHJ/CHS endpoints** — would unlock real-time hydrological data
5. **🟢 Index `RESUM RISCS CV.pdf` into Pinecone** — currently only in `processed_data/` as CSVs, not in semantic search

---

## 🧠 Data Extraction Strategy by Dataset

Here is exactly how we handle each of the 19 individual data links/sources:

### 🔴 Seismic Data
1. **`spaicv31_siscova_sismos` (GVA Siscova)**: 
   * **What:** Every recorded earthquake in the Comunitat Valenciana since 2022.
   * **How:** We built `siscova_earthquakes` to call the live GVA WFS (Web Feature Service) API. It parses the real-time CSV response in memory without downloading any files.
2. **`pelsiscav_anexo_b` (Historical Catalog)**:
   * **What:** 6,463 ancient earthquakes (1048–2009).
   * **How:** Since this was locked in a massive 45MB PDF, we ran a `pdfplumber` script to detect the grid lines and extract the tables into ~210 clean `.csv` files stored in `vault/csvs/`.
3. **`pelsiscav_anexo_e` (Intensity Tables)**:
   * **What:** Expected seismic intensity tables.
   * **How:** Handled exactly the same as Anexo B, extracted from the PDF into CSV tables.
4. **`siscova-stations` (Seismic Stations)**:
   * **What:** Locations and sensor types for the 11 active stations.
   * **How:** There is no API, so `siscova_scraper` downloads the raw HTML of the website and extracts the data row-by-row from the `<table>` tags into structured JSON.
5. **`ign-stations` (IGN Stations)**:
   * **Status:** 🟠 Not yet integrated. Needs research on whether the IGN provides a direct API or if we need to scrape their web viewer.
6. **`afon-alicante` (Univ. Alicante)**:
   * **Status:** ❌ Not automatable. This requires institutional access, so we would need to manually request a CSV from them and drop it into the `vault`.

### 🔵 Flood / Hydrological Data
7. **`spa_icv_orde_patricova_peligrosidad_inun` (Flood Hazard)**:
   * **What:** The official flood risk level for any GPS coordinate.
   * **How:** We built `patricova_flood_risk` to send lat/lon coordinates to the live ArcGIS REST API (Identify endpoint), letting their servers do the geospatial math. We also downloaded the entire raw GIS dataset as a huge static CSV (9.2MB) in `vault/csvs/`.
8. **`snczi-varios` (National Flood Zones)**:
   * **Status:** 🟠 Not yet integrated. We need to check if the MITECO web viewer exposes public WMS/WFS API endpoints.
9. **`ign-tsunamis` (Tsunami Catalog)**:
   * **Status:** ❌ Manual. Since this is a tiny static dataset (14 historical tsunamis), we would just download the CSV manually from the DOI link and drop it in the vault.
10. **`chj-opendata` (Júcar Basin)**:
    * **Status:** ✅ **Integrated**. All ~190 static infrastructure, flood risk, and pressure datasets (CSVs) have been downloaded and organized in `vault/csvs/CHJ_OpenData/`. WMS live map endpoints are stored in `CHJ_WMS_Endpoints.md`.
11. **`chs-opendata` (Segura Basin)**:
    * **Status:** 🟠 Not yet integrated. Same as above.

### 🌤️ Meteorological Data
12. **`aemet-forecast-marine` (Sea Forecast)**:
    * **Status:** ✅ **Integrated**. `aemet_marine` tool built. Supports coastal (Valencia & Murcia coast, code 46) and high-sea forecasts.
13. **`aemet-weather-atlas` (Climate Normals)**:
    * **Status:** ✅ **Integrated**. The new query types (normals, monthly, extremes) in the `aemet_historical` tool now cover all of this map data directly from the API.
14. **`aemet-forecast-weather` (Municipal Forecast)**:
    * **Status:** ✅ **Integrated**. `aemet_forecast` tool built. Daily (7-day) and hourly (48h) modes. Default: San Vicente del Raspeig (03122).
15. **`aemet-forecast` (General/Fire Risk)**:
    * **Status:** ✅ **Integrated**. `aemet_fire_risk` tool built. Supports estimated fire risk, forecast fire risk (1-7 days), and UV index (0-4 days).
16. **`aemet-opendata` (Historical Climate)**:
    * **Status:** ✅ **Integrated**. `aemet_historical` tool built. Supports real-time station observations and historical daily climate data with date ranges.

### 🌡️ Climate Projections
17. **`adaptecca-rcp-4.5-8.5` (AdapteCCa)**:
    * **Status:** ❌ Manual. Web viewer only. We must manually download the projection files (likely NetCDF) and convert them to CSVs.
18. **`pnacc-ar6` (AEMET Projections)**:
    * **Status:** ❌ Manual. Same as above.

### 🚨 Emergency / Risk Data
19. **`risk-cv` (Valencian Risk Tables)**:
    * **What:** Municipal risk levels (Floods, Fires, Seismic, etc.) for every town.
    * **How:** Locked in `RESUM RISCS CV.pdf`. We ran the `pdf_to_tables.py` script using `pdfplumber` to extract the 14 pages into 14 separate CSV files inside `vault/processed_data/`.
20. **`gva-112-info` (112CV Guidelines)**:
    * **What:** Text guidelines on emergency procedures.
    * **How:** We will use Semantic Search (Pinecone RAG). The PDFs/texts are chunked into 1,000-character pieces, embedded with Gemini, and stored in Pinecone. We extract the first 400 characters as a "resume" (summary) for the catalog so the Agent knows what the document is about before searching.

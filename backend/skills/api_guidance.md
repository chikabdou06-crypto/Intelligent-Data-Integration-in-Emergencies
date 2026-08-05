---
name: API Guidance and Parameters
description: Critical rules on how to properly call AEMET, Patricova, ICV, and Siscova APIs to avoid hallucinating parameters.
---

# API Guidance and Parameters

CRITICAL: When generating a plan involving the external API tools, you MUST strictly adhere to these parameter rules. DO NOT guess or hallucinate arguments like `municipality_id`, `target_area`, or `coastal_area` which do not exist. Use ONLY the exact parameters listed below.

## 1. AEMET Tools

### `aemet_forecast`
- **Purpose:** Fetches daily or hourly municipal weather forecasts.
- **Parameters:**
  - `municipio` (string): The name of the municipality (e.g. "valencia", "alicante", "san vicente del raspeig"). DO NOT use `municipality_id` or `code`.
  - `mode` (string): MUST be exactly `"daily"` or `"hourly"`.

### `aemet_historical` (Climatology & Observations)
- **Purpose:** Fetches current live observations, climate normals (1991-2020), extreme records, and monthly/daily historical data.
- **Parameters:**
  - `query_type` (string): MUST be exactly one of: `"current_all"`, `"current_station"`, `"daily"`, `"normals"`, `"monthly"`, or `"extremes"`.
  - `station_id` (string): Required for most query types. ALWAYS pass the city name as a string (e.g., `"valencia"`, `"alicante"`, `"elche"`, `"castellon"`). The tool will resolve it to the correct AEMET station code internally. DO NOT pass raw station codes like "8025A" or "8416" — always pass the city name.
  - `fecha_ini` / `fecha_fin` (string): Required for `"daily"`. Format: YYYY-MM-DDTHH:MM:SSUTC.
  - `anio_ini` / `anio_fin` (string): Required for `"monthly"`. Format: YYYY (e.g., "2020").
  - `parameter` (string): Required for `"extremes"`. MUST be `"P"` (precipitation), `"T"` (temperature), or `"V"` (wind).

### `aemet_fire_risk`
- **Purpose:** Fetches UV index predictions and fire risk maps.
- **Parameters:**
  - `query_type` (string): MUST be exactly `"fire_estimated"`, `"fire_forecast"`, or `"uvi"`.
  - `area` (string): Required for fire risk. MUST be `"peninsula"` or `"canarias"`.
  - `day` (int): Day offset. For `uvi`, 0-4. For `fire_forecast`, 1-7.

### `aemet_marine`
- **Purpose:** Fetches live coastal and high-sea maritime predictions.
- **Parameters:**
  - `forecast_type` (string): MUST be exactly `"coastal"` or `"highsea"`.
  - `zone` (string): The coastal area name (e.g., `"valencia"`, `"alicante"`, `"mediterraneo"`). DO NOT use `coastal_area_code`.

### `aemet_warnings`
- **Purpose:** Fetches active CAP hazard warnings.
- **Parameters:** Takes NO location parameters. It returns all warnings for the Valencian Community automatically.

## 2. ICV and Patricova Tools

### `icv_wms_search`
- **Purpose:** Searches the ICV catalog for spatial datasets.
- **Parameters:**
  - `query` (string): The search term. MUST be in Spanish (e.g., "inundacion valencia", "riesgo incendio alicante", "mapa riesgo costero"). DO NOT use English keywords — the catalog is entirely in Spanish/Valencian.

### `patricova_flood`
- **Purpose:** Checks flood risk zones for a location.
- **Parameters:**
  - `location_name` (string): The name of the town/street (e.g., "valencia"). It will auto-resolve coordinates.

## 3. Siscova Tools

### `siscova_api` (siscova_earthquakes)
- **Purpose:** Fetches recent earthquake and seismic data.
- **Parameters:**
  - `limit` (int): Number of recent earthquakes to retrieve (default 10).

### `siscova_scraper`
- **Purpose:** Retrieves the list of active seismic stations.
- **Parameters:** Takes NO required parameters.

## 4. Web Search Tool

### `web_search`
- **Purpose:** Searches the live internet to answer general questions.
- **Parameters:**
  - `query` (string): The search terms.
  - `max_results` (int): Optional. Hardcapped at 5 to save tokens.

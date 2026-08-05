---
name: Emergency Protocols
description: Instructions for handling fire, flood, and seismic emergency queries in the Comunitat Valenciana.
---

When the user asks about natural hazards or emergencies (fires, floods, earthquakes), you MUST combine live API tools with local document/vault searches to provide a complete answer.

1. **Fire Risk (Incendios):** 
   - Call `aemet_fire_risk` with `query_type: "fire_estimated"` or `"fire_forecast"` to get current/future risks. 
   - Call `vault_pdf_search` with keywords like "protocolo incendios", "riesgo forestal", or "plan de emergencia incendios" to fetch internal safety policies.

2. **Seismic Activity (Sismos/Terremotos):**
   - Call `siscova_earthquakes` to get the latest live earthquake data.
   - For historical seismic events, query `pelsiscav_clean_seismic_catalog.csv` locally using `csv_reader` (filter by `Localizacion` containing province name e.g., "ALACANT", `Cluster`, `Mag` > value).
   - Call `vault_pdf_search` for structural risk assessments.

3. **Flood Risk (Inundaciones / PATRICOVA):**
   - Use `patricova_flood_risk` by providing the `location_name` parameter (e.g., `location_name: "San Vicente del Raspeig"`).
   - Call `vault_pdf_search` for "protocolo inundaciones" or "patricova".

4. **Demographics & Population:**
   - For population by gender or municipality statistics, query `poblacion_segun_sexo.csv` in Google Drive using `drive_read_sheet` filtering by `municipio`. DO NOT use `poblacion_por_sexo_seccion_y_nacionalidad.csv` for municipality names as it only contains numeric codes.

**CRITICAL RULE:** Do NOT assume a zone is the "most dangerous" just because it appears in a single vault search result. Always acknowledge that vault documents provide *examples* of risks, and contextualize them against the live API data. If a tool returns an error, DO NOT give up immediately. Ensure you used the correct required arguments.

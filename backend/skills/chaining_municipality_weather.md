---
name: chaining-municipality-weather
description: Strict instructions for looking up municipality names and chaining data tools (like CSVs) into the AEMET weather forecast API.
---

# Municipality Lookup & API Chaining

When you need to look up a municipality name or INE code, or when you need to chain data from a CSV query into the AEMET weather forecast API, you MUST follow these strict rules.

## MUNICIPALITY NAME LOOKUP
To translate a province code + municipality code into an official name or INE code, use EXACTLY `relacion_municipios_comarcas_comunidad_valenciana.csv`.
- Useful columns: `cod_prov`, `cod_mun`, `código INE`, `municipio`.

## AEMET MUNICIPALITY CHAINING (CRITICAL)
When chaining from an economic/demographic CSV to `aemet_forecast`:

**STEP A:** Query the dataset (e.g., income/rental CSV) with `order_by` + `order_desc=true` + `max_rows=1` to find the target municipality.
**STEP B:** Query `relacion_municipios_comarcas_comunidad_valenciana.csv` to find its INE code.
   - Example filters: `filter_column="cod_mun", filter_value="$STEP_0.data.0.codigo_municipio", filter_column_2="cod_prov", filter_value_2="$STEP_0.data.0.codigo_provincia", max_rows=1`.
**STEP C:** Pass the resolved INE code to the AEMET forecast API.
   - Example: Pass `"$STEP_1.data.0.código INE"` as the `municipio` argument to `aemet_forecast`.

**WARNING:** NEVER pass a raw "Secciones" field (like the 10-digit census code "0301404026") or a partial 3-digit code like "014" directly to `aemet_forecast`. It MUST be a 5-digit INE code or a recognized municipality name.

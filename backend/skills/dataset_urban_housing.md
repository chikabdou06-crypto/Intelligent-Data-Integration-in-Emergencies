---
name: dataset-urban-housing
description: Strict instructions for querying urban, housing, and infrastructure datasets including waste containers, people per dwelling, and property counts.
---

# Urban, Housing & Infrastructure Dataset Skills

When the user asks about housing, dwellings, properties, waste containers, recycling, or urban infrastructure, you MUST use the following rules.

## WASTE CONTAINERS / RECYCLING
- Use EXACTLY `contenedores_procesados_final.csv`.
- Key columns: `MATRÍCULA`, `DIRECCION`, `NUMERO/ CRUCE`, `lat`, `lon`, `Direccion Completa`, `TIPO` (container type: "Envases", "Vidrio", "Orgánica", etc.), `NUM`, `MUN` (municipality code).
- This file contains **geolocated** container positions with `lat` and `lon`.
- Filter by container type using `TIPO`, or by municipality using `MUN`.

## PEOPLE PER DWELLING
- Use EXACTLY `personas_por_vivienda_personas_por_vivienda.csv`.
- Key columns: `id_edificio` (cadastral building ID), `seccion_censal` (census section code), `personas` (JSON array of people).
- **WARNING**: The `personas` column contains a JSON-like string with individual records (`genero`, `edad`, `nacionalidad`). This is NOT a simple numeric column — you cannot directly sort or aggregate it with `csv_reader`.
- Best approach: Use `csv_reader` with a `filter_column="seccion_censal"` filter to retrieve records for a specific area, then let the Synthesizer parse the `personas` field.

## PROPERTY COUNTS
- Use EXACTLY `numero_inmuebles.csv`.
- Key columns: `refcat` (cadastral reference), `direccion`, `calle`, `numero`.
- This file lists individual properties by address. For counting properties in an area, use `csv_aggregate` with `operation="count"`.

## CADASTRAL DATA (ADVANCED)
- **Rural parcels**: `Parcela_rustica.csv` (5.4 MB)
- **Urban parcels**: `Parcela_urbana.csv` (8 MB)
- **Rural polygons**: `Poligono_catastral_rustico.csv`
- **Urban polygons**: `Poligono_catastral_urbano.csv`
- **WARNING**: These files may contain geometry columns. Always use `exclude_columns="geometry"` to avoid bloating responses.

## VERY LARGE PROPERTY FILES (USE WITH CAUTION)
- `Datos_inmuebles_documento_procesado_geoinfo.csv` (~350 MB)
- `Datos_inmuebles_documento_procesado_geoinfo_seccion_censal.csv` (~350 MB)
- `Datos_construcciones_inmuebles_san_vicente.csv` (~5 MB)
- **WARNING**: The first two files are extremely large. Always apply tight filters (`filter_column` + `filter_value`) before reading. Never request all rows.

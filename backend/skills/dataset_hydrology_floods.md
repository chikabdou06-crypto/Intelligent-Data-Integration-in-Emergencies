---
name: dataset-hydrology-floods
description: Strict instructions for querying hydrology, flood risk, and flood hazard datasets including PATRICOVA flood zones, hydrographic stations, and river basin demarcations.
---

# Hydrology & Flood Risk Dataset Skills

When the user asks about floods, flood risk, flood hazard, river basins, hydrographic demarcations, water levels, or PATRICOVA, you MUST use the following rules.

## FLOOD RISK ZONES (PATRICOVA)
- Use EXACTLY `riesgo_inundaciones.csv`.
- Key columns: `geometry` (polygon), `riesgo` (risk level: "Bajo", "Medio", "Alto"), `area`, `fuente`.
- **WARNING**: This file contains massive geometry polygons. Always use `exclude_columns="geometry"` unless the user specifically asks for coordinates.
- **CRITICAL**: You CANNOT filter this file by municipality name — it only has geometry and risk level. To find flood risk for a specific municipality, use the `patricova_flood_risk` tool with the `location_name` parameter instead.
- Source: PATRICOVA (Plan de Acción Territorial sobre Prevención del Riesgo de Inundación en la Comunitat Valenciana).

## FLOOD HAZARD CLASSIFICATION
- Use EXACTLY `peligrosidad_inun.csv`.
- Key columns: `codigo`, `zona`, `d_pelig` (hazard description), `n_pelig` (hazard level 1-7), `corriente` (river/stream name), `tipo`, `calado` (flood depth), `retorno` (return period in years), `demarcacion` (hydrographic demarcation), `geometry`.
- **WARNING**: Contains geometry column. Always use `exclude_columns="geometry"`.
- Hazard descriptions include: "Peligrosidad Geomorfológica: Abanicos torrenciales", "Frecuencia alta", "Frecuencia media", etc.
- To find the most dangerous flood zones, sort by `n_pelig` descending (`order_by="n_pelig"`, `order_desc=true`).

## HYDROGRAPHIC DEMARCATIONS
- Use EXACTLY `demarcaciones_hidograficas.csv`.
- Contains hydrographic basin zones and boundaries.
- **WARNING**: Contains geometry column. Always use `exclude_columns="geometry"`.

## JUCAR BASIN MONITORING STATIONS
- Use EXACTLY `estaciones_hidrologicas_jucar.csv`.
- Contains location data for hydrological monitoring stations in the Júcar river basin.
- Key columns: station identifiers, coordinates, and basin association.

## PATRICOVA FLOOD RISK TOOL (LIVE API)
- When the user asks "What is the flood risk for [municipality]?", prefer the `patricova_flood_risk` tool over the CSV.
- Pass the municipality name directly as the `location_name` parameter.
- This tool returns structured risk levels without needing to parse geometry polygons.

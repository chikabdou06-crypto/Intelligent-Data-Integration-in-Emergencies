---
name: dataset-seismic
description: Strict instructions for querying and interacting with seismic, earthquake, and PELSISCAV datasets.
---

# Seismic Dataset Skills

When the user asks for historical or live earthquake data, you MUST use the following rules to query the resources accurately:

## HISTORICAL EARTHQUAKES (PELSISCAV)
- For historical earthquakes, use EXACTLY `pelsiscav_clean_seismic_catalog.csv`.
- This dataset contains historical macroseismic records and instrumental catalogs.
- Key columns include: `Fecha`, `Hora`, `Lat`, `Long`, `Prof`, `Int`, `Mag`, `Localizacion`, `Cluster`.

## LIVE REAL-TIME EARTHQUAKES (SISCOVA)
- For live, real-time, or very recent seismic events, do NOT use the CSV.
- Instead, use the `siscova_earthquakes` tool.

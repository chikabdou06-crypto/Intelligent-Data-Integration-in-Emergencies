---
name: dataset-public-safety
description: Strict instructions for querying crime and public safety datasets including general crime, conventional crime, robberies, sexual crimes, and cybercrime.
---

# Public Safety & Crime Dataset Skills

When the user asks about crime, public safety, criminality, robberies, sexual offenses, or cybercrime, you MUST use the following rules.

## GENERAL CRIME OVERVIEW
- Use EXACTLY `criminalidad_general.csv`.
- This file has high-level crime totals per municipality per year.

## CONVENTIONAL CRIME (DETAILED)
- Use EXACTLY `criminalidad_convencional.csv`.
- This file has a breakdown of conventional crime types per municipality.

## ROBBERIES
- Use EXACTLY `criminalidad_convencional_robos.csv`.

## SEXUAL CRIMES
- Use EXACTLY `criminalidad_convencional_sexual.csv`.

## CYBERCRIME
- Use EXACTLY `criminalidad_ciberdelincuencia.csv`.

## COMMON SCHEMA (ALL 5 FILES)
All five crime files share the SAME column schema:
- `tipologia_penal`: The type of crime (e.g. "HURTOS", "ROBOS CON FUERZA", "TOTAL INFRACCIONES PENALES").
- `provincia`: Province code (e.g. "03" for Alicante).
- `cod_mun`: Municipality code (e.g. "014" for Alicante city).
- `q1`, `q2`, `q3`, `q4`: Crime counts per **quarter** (NOT per month).
- `year`: The year (e.g. "2023").

### CRITICAL RULES
1. **Data is QUARTERLY, not monthly.** There are NO monthly breakdowns. If the user asks for "January crime data", explain that the finest granularity is quarterly (`q1` = January-March).
2. To get the total annual crime for a municipality, you must **SUM q1 + q2 + q3 + q4**. There is no pre-computed annual total column.
3. Filter by municipality using `cod_mun` (NOT by name). To translate a name to a code, use `relacion_municipios_comarcas_comunidad_valenciana.csv`.
4. Filter by crime type using `tipologia_penal`. Use `contains` operator since values can be long strings.
5. To find the municipality with the highest crime, sort by `q1` (or whichever quarter is relevant), or use `csv_aggregate` to sum all quarters.

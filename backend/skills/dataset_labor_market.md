---
name: dataset-labor-market
description: Strict instructions for querying labor market datasets including employment contracts, Social Security affiliates, job seekers, and occupation/activity breakdowns.
---

# Labor Market Dataset Skills

When the user asks about employment, contracts, job seekers, Social Security affiliates, occupations, economic sectors, or professional situations, you MUST use the following rules.

## EMPLOYMENT CONTRACTS
- Use EXACTLY `contratos_2006_2025.csv`.
- **CRITICAL FILTERING RULE**: Filter dates using `anyo` (e.g. "2024") and `mes` (e.g. "01"). **NEVER use text months like "Enero".**
- Municipality filter: use `Codigo Municipio` (e.g. "014") and `Codigo Provincia` (e.g. "03").
- **WARNING**: The municipality column has a leading space: ` Municipio` (with a space before "Municipio"). Use `Codigo Municipio` for reliable filtering instead.
- Key metric columns: `Total Contratos`, `Contratos iniciales indefinidos hombres`, `Contratos iniciales temporales hombres`, `Contratos iniciales indefinidos mujeres`, `Contratos iniciales temporales mujeres`, `Contratos  Agricultura`, `Contratos  Industria`, `Contratos Construcción`, `Contratos  Servicios`.
- To find the municipality with the most/least contracts, sort by `Total Contratos`.
- **WARNING**: Columns with `censored_` prefix indicate statistical confidentiality flags. Ignore them for analysis.

## SOCIAL SECURITY AFFILIATES (EMPLOYED PEOPLE)
- Use EXACTLY `afiliados_2022_2025.csv`.
- **CRITICAL FILTERING RULE**: This file has `year` and `month` columns (e.g. "2024", "06"). Use these for date filtering.
- Municipality filter: use `COD MUNICIPIO` (e.g. "014") and `COD PROVINCIA` (e.g. "03").
- **NOTE**: Column names are UPPERCASE: `MUJER`, `VARON`, `REGIMEN`, `MUNICIPIO`.
- Data is broken down by `REGIMEN` (Social Security regime). To get total affiliates for a municipality, you may need to use `csv_aggregate` with `aggregate_columns="MUJER"` or `"VARON"` and `group_by="MUNICIPIO"`.

## JOB SEEKERS / LABOR DEMAND
- Use EXACTLY `demandantes_2008_2025.csv`.
- **CRITICAL FILTERING RULE**: Filter dates using `anyo` (e.g. "2024") and `mes` (e.g. "01"). **NEVER use text months.**
- Municipality filter: use `Codigo Municipio` and `Codigo Provincia`.
- Key metric columns: `total Dtes Empleo`, plus breakdowns by age/sex (`Dtes Empleo hombre edad < 25`, `Dtes Empleo mujer edad >= 45`, etc.) and by sector (`Dtes EmpleoAgricultura`, `Dtes Empleo Industria`, `Dtes Empleo Construcción`, `Dtes Empleo Servicios`).

## OCCUPATION BY SEX (Census)
- Use EXACTLY `Sexo_y_ocupacion_limpio.csv`.
- Filter by `Periodo` (e.g. "2021", "2022") and optionally `Ocupación`.
- Municipality filter: use `codigo_municipio` and `codigo_provincia`.

## ECONOMIC SECTOR / ACTIVITY BY SEX (Census)
- Use EXACTLY `Sexo_y_rama_actividad_limpio.csv`.
- Filter by `Periodo` and optionally `Actividad económica`.
- Municipality filter: use `codigo_municipio` and `codigo_provincia`.

## ACTIVITY STATUS BY SEX (Census)
- Use EXACTLY `Sexo_y_relacion_con_la_actividad.csv`.
- Filter by `Periodo` and optionally `Relación con la actividad`.
- Municipality filter: use `codigo_municipio` and `codigo_provincia`.

## PROFESSIONAL SITUATION BY SEX (Census)
- Use EXACTLY `Sexo_y_situacion_profesional_limpio.csv`.
- Similar schema to other census files above.

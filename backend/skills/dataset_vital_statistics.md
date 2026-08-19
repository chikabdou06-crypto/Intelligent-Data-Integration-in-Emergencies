---
name: dataset-vital-statistics
description: Strict instructions for querying vital statistics datasets including deaths, births, population by sex, population by nationality, and population by country of birth.
---

# Vital Statistics Dataset Skills

When the user asks about deaths, mortality, births, natality, population counts by sex, population by nationality, or population by country of birth, you MUST use the following rules.

## DEATHS / MORTALITY
- Use EXACTLY `muertes_por_sexo_y_municipio_de_residencia.csv`.
- Key columns: `municipio` (name), `ine_cod` (INE code), `year`, `mujeres`, `hombres`, `Total`, `cod_mun`, `cod_provincia`.
- Filter by year using `year` (e.g. "2022").
- Filter by municipality using `cod_mun` and `cod_provincia`, or use `municipio` with `contains` operator.

## BIRTHS / NATALITY
- Use EXACTLY `nacidos_segun_sexo_por_municipio_de_residencia_de_la_madre.csv`.
- Key columns: `municipio`, `ine_cod`, `year`, `mujeres`, `hombres`, `cod_mun`, `cod_provincia`, `fuente`.
- **NOTE**: This file does NOT have a `Total` column. To get total births, you must sum `mujeres` + `hombres` manually or use `csv_aggregate`.
- Filter by year using `year`.

## POPULATION BY SEX
- Use EXACTLY `poblacion_segun_sexo.csv`.
- Key columns: `municipio`, `ine_cod`, `year`, `mujeres`, `hombres`, `Total`, `cod_mun`, `cod_provincia`.
- This is the simplest population file — use it for total population counts by municipality and year.

## POPULATION BY NATIONALITY (Census Sections)
- Use EXACTLY `poblacion_por_sexo_seccion_y_nacionalidad.csv`.
- **WARNING**: This is a LARGE file (25 MB). Always use filters to avoid returning too many rows.
- Filter by `codigo_municipio`, `codigo_provincia`, and optionally `Nacionalidad`.

## POPULATION BY COUNTRY OF BIRTH (Census Sections)
- Use EXACTLY `poblacion_por_sexo_seccion_y_pais_de_nacimiento.csv`.
- **WARNING**: This is a LARGE file (27 MB). Always use filters.
- Filter by `codigo_municipio`, `codigo_provincia`, and optionally country of birth.

## NATIONALITIES REFERENCE TABLE
- Use EXACTLY `nacionalidades.csv`.
- Contains: `Nacionalidad`, `País`, `Continente`, `Agrupación`.
- Use this to translate nationality names or group by continent.
- **WARNING**: This file contains a `geometry` column — use `exclude_columns="geometry"` to avoid bloating responses.

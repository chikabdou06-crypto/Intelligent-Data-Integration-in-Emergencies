---
name: dataset-demographics
description: Strict instructions for filtering and querying demographic datasets including education, population statistics, census indicators, and padron data.
---

# Demographics Dataset Skills

When the user asks for demographic data (education, population, census indicators, or padron records), you MUST use the following rules to query the local CSV files accurately:

## EDUCATION (by Country of Birth)
- Use EXACTLY `pais_nacimiento_y_nivel_estudios.csv`.
- Key columns: `Nivel de formación alcanzado`, `Periodo`, `codigo_municipio`, `codigo_seccion`, `codigo_provincia`, `España` (count of Spanish-born), `Extranjera` (count of foreign-born).
- Education levels include: "Educación primaria e inferior", "Primera etapa de educación secundaria y similar", "Segunda etapa de educación secundaria y educación postsecundaria no superior", "Educación superior".
- **WARNING**: Some small municipalities have `.` (period) instead of a number in the `España`/`Extranjera` columns (statistical suppression for privacy). These rows will sort as strings, not numbers.

## EDUCATION (by Sex)
- Use EXACTLY `Sexo_y_nivel_estudios.csv`.
- Similar schema but broken down by sex (Hombres/Mujeres) instead of by country of birth.

## ACTIVITY STATUS (by Country of Birth)
- Use EXACTLY `pais_nacimiento_y_relacion_con_la_actividad.csv`.
- Combines nationality (España/Extranjera) with activity status (employed, unemployed, inactive).

## CENSUS SECTION DEMOGRAPHIC INDICATORS
- Use EXACTLY `Indicadores_demograficos_secciones.csv`.
- Key columns: `Secciones` (census section code), `Periodo`, `codigo_municipio`, `codigo_seccion`, `codigo_provincia`, `Edad media de la población`, `Población`, `Porcentaje de hogares unipersonales`, `Porcentaje de población de 65 y más años`, `Porcentaje de población española`, `Porcentaje de población menor de 18 años`, `Tamaño medio del hogar`.
- **This is the BEST file for questions about aging, population size, household size, or age distribution at the census section level.**

## MUNICIPAL DEMOGRAPHIC INDICATORS
- Use EXACTLY `indicadores_demograficos_municipales.csv`.
- Contains aggregated demographic indicators at the municipal level (as opposed to census section level).
- Use this when the user asks about municipality-wide demographics rather than specific neighborhoods.

## POPULATION BY SEX AND AGE (Census Sections)
- Use EXACTLY `poblacion_por_sexo_seccion_y_edad.csv`.
- **WARNING**: This is a LARGE file (11 MB). Always use filters.
- Contains population broken down by sex and age ranges per census section.

## PADRON CONTINUO (San Vicente del Raspeig)
- Use EXACTLY `padron_continuo_san_vicente_raspeig.csv`.
- **NOTE**: This file ONLY covers San Vicente del Raspeig. Do NOT use it for other municipalities.
- Contains continuous census register data with detailed demographic breakdowns.

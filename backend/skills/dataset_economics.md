---
name: dataset-economics
description: Strict instructions for filtering and querying economic datasets including income, rental, unemployment, and pensions.
---

# Economics Dataset Skills

When the user asks for economic data (income, rental prices, unemployment, or pensions), you MUST use the following rules to query the local CSV files accurately:

## INCOME / RENTA DATA
- The **ONLY** file containing average income per person is EXACTLY `distribucion_por_fuente_de_ingresos.csv`.
- Target Column: `Renta bruta media por persona`.
- **WARNING**: `Indicadores_renta_secciones_censales.csv` contains only INEQUALITY indices (Gini, P80/P20), **NOT** absolute income figures.
- **NEVER** invent filenames like `renta_media_hogar.csv`. If it's not in the Vault Catalog, it doesn't exist.

## RENTAL / ALQUILER DATA
- For **Alicante 2022** rental prices, use EXACTLY `ALQ_Secciones_2022_Alicante.csv`.
- Target Column: `mediana_cuantia_mensual_vivienda_colectiva`.
- For **historical/region-wide** rental data, use `historico_alquileres_octubre_2024.csv`.

## UNEMPLOYMENT / PARO
- Use EXACTLY `paro_2008_2025.csv`.
- **CRITICAL FILTERING RULE**: Filter dates using `anyo` (e.g. "2025") and `mes` (e.g. "01"). **NEVER use text like "Enero" for the month filter.**
- To find the maximum or sort, sort by the column `total Paro Registrado`.

## PENSIONS (CONTRIBUTIVAS)
- Use EXACTLY `pensiones_contributivas_vigor_alicante_historico.csv`.
- Target Column: `pensionistas` (You MUST pass this as the `aggregate_columns` argument).
- **CRITICAL FILTERING RULE**: This file **ONLY** contains Alicante data, so **DO NOT filter by province** (if you try to filter by 'Alicante', it will fail because the province code is '03').
- You **MUST** filter by `year` (e.g. "2024") and `trimestre` (e.g. "1") when using `csv_aggregate` to avoid accidentally summing up all historical totals together.

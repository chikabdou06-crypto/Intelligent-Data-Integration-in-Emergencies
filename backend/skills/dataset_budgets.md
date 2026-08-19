---
name: dataset-budgets
description: Strict instructions for querying municipal budget datasets including expenditure by area, initial budget credits, and revenue forecasts.
---

# Municipal Budget Dataset Skills

When the user asks about municipal budgets, public spending, government expenditure, debt, taxes, revenue, or fiscal data, you MUST use the following rules.

## BUDGET EXPENDITURE BY AREA
- Use EXACTLY `Area_gasto_presupuesto.csv`.
- Key columns:
  - `pr`: Province code (e.g. "03" = Alicante).
  - `cor`: Municipality code (e.g. "014" = Alicante city).
  - `año`: Year (e.g. "2023").
  - `deuda_pública`: Public debt.
  - `servicios_públicos_básicos`: Basic public services.
  - `actuaciones_de_protección_y_promoción_social`: Social protection spending.
  - `producción_de_bienes_públicos_de_carácter_preferente`: Education, culture, health.
  - `actuaciones_de_carácter_económico`: Economic activities.
  - `actuaciones_de_carácter_general`: General administration.
  - `total_gastos`: **Total expenditure** (use this for ranking municipalities by spending).
- **CRITICAL**: Filter by year using `año`, by province using `pr`, and by municipality using `cor`.

## INITIAL BUDGET CREDITS (EXPENDITURE BREAKDOWN)
- Use EXACTLY `Creditos_inicales_presupuestos.csv`.
- Key columns:
  - `pr`, `cor`, `año`: Same as above (province code, municipality code, year).
  - `gastos_de_personal`: Personnel costs.
  - `gastos_en_bienes_ctes._y_servicios`: Current goods and services.
  - `gastos_financieros`: Financial expenses.
  - `inversiones_reales`: Real investments (capital expenditure).
  - `total_gastos_créditos`: **Total budget credits**.

## REVENUE FORECASTS (INCOME BREAKDOWN)
- Use EXACTLY `Prevision_inicales_presupuestos.csv`.
- Key columns:
  - `pr`, `cor`, `año`: Same as above.
  - `impuestos_directos`: Direct taxes.
  - `impuestos_indirectos`: Indirect taxes.
  - `tasas_y_otros_ingresos`: Fees and other revenue.
  - `transferencias_corrientes`: Current transfers (grants from higher government).
  - `ingresos_patrimoniales`: Property income.
  - `total_ingresos`: **Total revenue** (use this for ranking).

## COMMON RULES FOR ALL 3 BUDGET FILES
1. **`pr` = Province Code, `cor` = Municipality Code.** These are NOT full names. To translate a name to codes, use `relacion_municipios_comarcas_comunidad_valenciana.csv`.
2. **All monetary values are in thousands of euros (€).** Clarify this to the user.
3. To compare spending vs. revenue, chain `Area_gasto_presupuesto.csv` (Step 1, get `total_gastos`) with `Prevision_inicales_presupuestos.csv` (Step 2, get `total_ingresos`) for the same `pr`, `cor`, and `año`.

---
name: csv-cross-reference
description: Multi-step data analysis across one or more local CSV files. Covers filtering, sorting, aggregating, and joining results across multiple datasets using $PREV and $STEP_X chaining. Use when the user asks to find, rank, compare, or calculate something from the local vault CSV datasets — especially when the answer requires data from more than one file.
---

# CSV Cross-Reference & Multi-Dataset Analysis

End-to-end workflow for answering questions that span one or more CSV files from the local data vault. Execute each step precisely — never guess column names or skip steps.

## When to Use This Skill

**Activation Triggers**:
- "Find the [X] with the highest / lowest [column]"
- "What is the total / average / sum of [column] for [entity]?"
- "How many [column] in [file] for [filter]?"
- "Compare [entity] across [file1] and [file2]"
- "Look up [thing] in [file], then find related data in [other file]"
- Any question requiring data from more than one local CSV dataset

**Do NOT use** for:
- Questions about live data (use `aemet_forecast`, `aemet_warnings` tools instead)
- Questions about graph relationships (use `graph-reasoning` skill instead)
- Questions answerable by a single file read with no chaining

---

## Phase 1: Discover Available Data

**When**: User prompt references a dataset you are not 100% certain exists, or mentions a topic without naming a file.

**Objective**: Identify the exact filename(s) and column names to use.

### Tool: `csv_list`
- **Input**: None
- **Output**: Dict of `{filename: {columns: [...], file_size_bytes: N}}`
- **Use**: Get all available CSV files and their exact column headers before any query

### Tool: `vault_catalog`
- **Input**: None
- **Output**: Summary of all indexed CSVs and PDFs
- **Use**: Alternative discovery when you need a higher-level description of the data

### Decision Logic

| Condition | Action |
|-----------|--------|
| Filename explicitly stated by user | Skip to Phase 2 directly |
| User says "unemployment data" or similar | Run `csv_list`, pick the most relevant filename |
| You are unsure which column to filter by | Run `csv_list` to inspect headers, then proceed |
| File does not exist in vault | Report to user — do NOT hallucinate a filename |

---

## Phase 2: Find a Specific Entity (Sorting / Ranking)

**When**: The prompt asks for the entity with the highest, lowest, most, or least of some column.

**Objective**: Retrieve the single row (or top N rows) that satisfies the ranking criterion.

### Tool: `csv_reader`

| Parameter | Value | Notes |
|-----------|-------|-------|
| `filename` | `"Info_Municipios.csv"` | Exact filename including extension |
| `order_by` | `"viviendas_totales"` | Exact column name — case-sensitive |
| `order_desc` | `true` | `true` = descending (highest first), `false` = ascending (lowest first) |
| `max_rows` | `1` | Use `1` to get only the top entity |

**Output format**: `{status, data: [{col1: val1, col2: val2, ...}], total_rows, ...}`

### Critical Rules

- **NEVER use `csv_aggregate` to find max/min rows.** It computes a single number — it cannot tell you *which* entity is the max. Use `csv_reader` with `order_by` instead.
- `order_by` performs numeric sort when values are numeric. It also strips commas from numbers like `"1.234,56"` automatically.
- If `total_rows: 0` is returned, your `filter_column`/`filter_value` did not match anything. See Fallback Strategies.

### Decision Logic

| Condition | Action |
|-----------|--------|
| Need the single highest value | `order_desc: true`, `max_rows: 1` |
| Need the top 5 entities | `order_desc: true`, `max_rows: 5` |
| Need the lowest value | `order_desc: false`, `max_rows: 1` |
| Column name is uncertain | Run `csv_list` first to confirm exact name |

---

## Phase 3: Aggregate Across All Rows (Sum / Count / Avg)

**When**: The prompt asks for a total, sum, count, or average — especially across thousands of rows.

**Objective**: Compute a numeric aggregation across all matching rows of a large CSV. Bypasses the row cap.

### Tool: `csv_aggregate`

| Parameter | Value | Notes |
|-----------|-------|-------|
| `filename` | `"paro_2008_2025.csv"` | Exact filename |
| `aggregate_columns` | `"total Paro Registrado"` | Exact column name — preserves spaces |
| `operation` | `"sum"` | One of: `sum`, `count`, `avg`, `min`, `max` |
| `filter_column` | `"Municipio"` | Column to filter on (optional) |
| `filter_value` | `"Alicante/Alacant"` | Value to filter — uses case-insensitive substring match |
| `group_by` | `null` | Optional: group results by a column |

**Output format**:
```
{status, results: {"__ALL__": {"total Paro Registrado": 4521789.0}}, total_rows_processed: 220, non_numeric_skipped: 0}
```

To access the result in a later step: `$STEP_N.results.__ALL__.[column name]`

### Decision Logic

| Condition | Action |
|-----------|--------|
| Need total across all years | `filter_column + filter_value`, no `group_by` |
| Need per-year totals | Set `group_by: "Año"` or equivalent date column |
| `total_rows_processed: 0` | Filter matched nothing — check filter value spelling |
| `non_numeric_skipped > 0` | Some rows had non-numeric data in that column — result is still valid for numeric rows |

---

## Phase 4: Filter and Read Rows

**When**: The prompt asks to look up specific data for a known entity, or retrieve demographic/detail data after finding an entity in a previous step.

**Objective**: Retrieve matching rows from a CSV given a known identifier.

### Tool: `csv_reader`

| Parameter | Value | Notes |
|-----------|-------|-------|
| `filename` | `"poblacion_segun_sexo.csv"` | Exact filename |
| `filter_column` | `"municipio"` | Column to match — case-sensitive column name |
| `filter_value` | `"$PREV.data.0.nombre"` | Can use $PREV or $STEP_X injection (see Phase 5) |
| `max_rows` | `500` (default) | Increase if you need more rows |
| `columns_only` | `false` | Set `true` to get headers only |
| `exclude_columns` | `"geometry,geom"` | Comma-separated columns to drop |

**Filter matching**: Case-insensitive substring. `"alicant"` matches `"Alicante/Alacant"`.

### Decision Logic

| Condition | Action |
|-----------|--------|
| Returned `total_rows: 0` | Filter value did not match — check spelling, try shorter substring |
| Need only headers | Set `columns_only: true` |
| Row data contains huge geometry columns | Set `exclude_columns: "geometry"` |
| Need a specific year from the results | Let the Synthesizer extract the year from the returned rows |

---

## Phase 5: Cross-Step Variable Chaining

**When**: Any step after Step 0 needs to use a value from a previous step's output.

**Objective**: Inject dynamic values from prior tool outputs into later step arguments.

### Syntax Reference

| Token | Meaning | Example |
|-------|---------|---------|
| `$PREV.path.to.field` | Smart backward search — scans ALL prior steps from newest to oldest until it finds the value | `$PREV.data.0.nombre` |
| `$STEP_0.path` | Explicitly reference Step 0's result | `$STEP_0.data.0.nombre` |
| `$STEP_1.path` | Explicitly reference Step 1's result | `$STEP_1.results.__ALL__` |

### Path Navigation

The path uses dot-notation:
- `data` → the `data` key in the result dict
- `data.0` → first item in the `data` array
- `data.0.nombre` → the `nombre` field of the first item

**NEVER use bracket notation**: `$STEP_0['nombre']` is **WRONG**. Write `$STEP_0.data.0.nombre`.

### Prefer $PREV When Possible

`$PREV` uses smart backwards search — the Orchestrator searches backwards through all steps until it finds the requested path. This means even if Step 1 doesn't have `nombre` (e.g., it's an aggregate result), `$PREV` will keep looking and find it in Step 0.

Use `$STEP_N` only when you need to target a *specific* step explicitly.

---

## Phase 6: Final Synthesis Instructions

After all tools have executed, the Synthesizer LLM will receive the full execution trace. Guide it to:

1. If a step returned `total_rows: 0` or `status: error`, explain what went wrong and why (e.g., name mismatch between datasets).
2. If the question asks for a specific sub-field (e.g., "men in 2024"), scan the returned rows for `year == 2024` and extract the `hombres` value.
3. If aggregate results are in `results.__ALL__.[column]`, extract and format that number.
4. Always state which dataset the final answer came from.

---

## Tool Parameter Reference (Common Mistakes)

| Tool | Parameter | Correct | Common Mistake |
|------|-----------|---------|----------------|
| `csv_reader` | `order_by` | `"viviendas_totales"` | `"viviendas totales"` (underscore matters) |
| `csv_aggregate` | `aggregate_columns` | `"total Paro Registrado"` | `"total_paro_registrado"` (original has spaces) |
| `csv_reader` | `filter_value` | `"Alicante/Alacant"` | `"alicante"` (works due to substring match, but be precise) |
| `csv_reader` | `order_desc` | `true` / `false` (boolean) | `"true"` (string — will be ignored) |
| `csv_reader` | `max_rows` | `1` (integer) | `"1"` (string) |

---

## Fallback Strategies

| Problem | Primary | Fallback |
|---------|---------|----------|
| Filter returns 0 rows | Check exact column name with `csv_list`, retry with different casing | Try shorter substring filter (e.g., `"Alicant"` instead of `"Alicante/Alacant"`) |
| Column name uncertain | Run `csv_list` first | Use `columns_only: true` on the target file |
| Aggregation returns 0 processed rows | Check `filter_column` spelling | Remove filter and aggregate the whole file, then Synthesizer filters |
| `$PREV` resolves to null | Use `$STEP_0` explicitly | Check that the prior step actually returned data at that path |

---

## Completeness Checklist

Before answering, verify:

- [ ] Correct filename(s) confirmed (not guessed)
- [ ] Column names verified against actual headers
- [ ] Sorting done with `csv_reader` + `order_by`, NOT with `csv_aggregate`
- [ ] Cross-step values injected with `$PREV` or `$STEP_N` dot-notation
- [ ] Fallback attempted if any step returned 0 rows
- [ ] Synthesizer extracts the specific value requested (year, sex, etc.) from returned rows
- [ ] Source dataset named in the final answer

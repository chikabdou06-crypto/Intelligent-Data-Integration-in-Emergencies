# Evaluation Scripts and Empirical Benchmarks

This directory contains the testing harness, benchmark suites, and evaluation scripts used to generate the empirical results and performance metrics reported in the Master's Thesis (*"Intelligent Data Integration in Emergencies"*).

All generated metric summaries and publication-quality plots are stored in the [`scripts/results/`](./results/) subfolder.

---

## Directory Structure

```text
scripts/
├── README.md                  # This documentation guide
├── run_thesis_benchmarks.py   # Primary 8-pillar academic benchmark suite
├── run_eval.py                # Automated functional test runner
├── dump_detailed_report.py    # Raw execution trace and plan dumper
├── eval_cases.json            # Reference test queries and expected tool bindings
└── results/                   # Benchmark outputs, metric JSONs, and figures
    ├── benchmark_results.json # Full numerical summary of all benchmark runs
    ├── *.png / *.pdf          # Standalone publication-grade evaluation charts
    ├── eval_report.md         # Generated markdown report from run_eval.py
    └── detailed_test_report.md# Raw planner and synthesis execution traces
```

---

## 1. Primary Benchmark Suite (`run_thesis_benchmarks.py`)

### Overview
`run_thesis_benchmarks.py` is the comprehensive empirical benchmark suite developed specifically for Master's Thesis (TFM) evaluation committees and external reviewers. It evaluates the agent against the **8 fundamental academic evaluation pillars**:

1. **Standalone BLEU Suite (BLEU-1, BLEU-2, BLEU-4)**: Evaluates n-gram lexical precision with Papineni et al. (2002) brevity penalty and Chen & Cherry (2014) NIST smoothing.
2. **Standalone ROUGE Suite (ROUGE-1, ROUGE-2, ROUGE-L)**: Measures factual and structural recall using Longest Common Subsequence (LCS) (Lin, 2004).
3. **Factual Grounding & Numerical/Entity Exact Match (NEM)**: Evaluates whether retrieved census numbers, INE codes, rainfall values, and hazard tiers match verified ground-truth values without hallucinations.
4. **Agentic Tool-Calling & DAG Planning (ToolLLM / BFCL)**: Measures Tool Precision, Recall, F1-Score, AST argument match, and topological graph validity.
5. **Progressive Skill Injection Efficiency**: Quantifies prompt token reduction and routing accuracy achieved by dynamically injecting matched domain skills vs. static catalog bloating.
6. **Isolated LLM Judge Fault Recovery**: Analyzes the self-healing rate of the orchestrator when recovering from runtime parameter exceptions in a clean context window ($T=0.0$).
7. **Systems Performance & Cache Speedup**: Measures cold-start latency percentiles ($P_{50}, P_{90}, P_{95}$) and benchmarks the sub-millisecond ($0.52\text{ ms}$) SQLite SHA-256 cache speedup factor ($\sim 17,556\times$).
8. **Cloud Frontier (Gemini 2.5 Flash) vs. Local Air-Gapped (Ollama Qwen 2.5 7B)**: Compares accuracy, latency, and hallucination trade-offs between cloud APIs and local on-premise models.

### Execution
```bash
python scripts/run_thesis_benchmarks.py
```

### Outputs
- Writes full structured metrics to `scripts/results/benchmark_results.json`.
- Generates 300 DPI publication plots in `scripts/results/`:
  - `bleu_comparison_chart.png` (Lexical precision breakdown across query tiers)
  - `rouge_comparison_chart.png` (Structural & factual recall breakdown)
  - `agentic_grounding_benchmark.png` (Tool-calling F1, AST match, NEM, CGR)
  - `latency_and_token_benchmark.png` (Latency percentiles and prompt token savings)

---

## 2. Functional Test Runner (`run_eval.py`)

### Overview
Automated regression and functional testing harness. It loads test queries from `eval_cases.json`, initializes the Model Context Protocol (MCP) client, executes the full pipeline (`generate_plan` $\rightarrow$ `execute_plan` $\rightarrow$ `generate_synthesis`), and verifies whether the expected tools were called without runtime crashes.

### Execution
```bash
python scripts/run_eval.py
```

### Outputs
- Outputs summary test statistics to the console.
- Generates `scripts/results/eval_report.md` logging status (`PASS`/`FAIL`), execution latency, and synthesis snippets for each case.

---

## 3. Raw Execution Trace Dumper (`dump_detailed_report.py`)

### Overview
A diagnostic inspection tool that executes benchmark queries and dumps the raw intermediate JSON structures:
- The JSON plan emitted by `planner.py`.
- The raw structured tool payload returned by `orchestrator.py` via MCP.
- The final response synthesized by `synthesis.py`.

### Execution
```bash
python scripts/dump_detailed_report.py
```

### Outputs
- Generates `scripts/results/detailed_test_report.md` for peer review and auditability.

---

## 4. Test Queries Battery (`eval_cases.json`)

Contains curated natural language test queries spanning:
- Single-source weather forecasts (AEMET OpenData API).
- Municipal socioeconomic lookups (INE census & employment spreadsheets).
- Multi-source spatial hazard evaluation (PATRICOVA flood polygons + AEMET CAP alerts).
- Cross-database relational joins (San Vicente del Raspeig demographic data).
- Out-of-scope negative control queries (testing 100% fast rejection).


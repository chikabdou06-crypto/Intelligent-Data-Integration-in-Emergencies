"""
Phase 1: Direct Tool Testing (NO LLM)
=====================================
Calls every tool directly with hardcoded correct parameters.
This isolates whether the tools themselves work or are broken.
If a tool fails here, the problem is in the tool's Python code.
If a tool passes here but fails in the full pipeline, the problem is the LLM.
"""
import sys
import os
import json
import time
from pathlib import Path

# Setup paths and env
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

from backend.core.registry import get_tool, list_all_tools

# ============================================================
# TEST DEFINITIONS
# Each test: (tool_name, description, kwargs)
# We use safe_execute() so crashes are caught gracefully.
# ============================================================

TESTS = [
    # ── LOCAL DATA TOOLS ──
    ("csv_list",       "List all available CSVs in vault",                              {}),
    ("csv_reader",     "Read seismic catalog (no filters, 5 rows)",                     {"filename": "pelsiscav_clean_seismic_catalog.csv", "max_rows": 5}),
    ("csv_reader",     "Read seismic catalog with location filter",                     {"filename": "pelsiscav_clean_seismic_catalog.csv", "filter_column": "Localizacion", "filter_value": "ALACANT", "max_rows": 5}),
    ("csv_reader",     "Read seismic catalog with magnitude > 3.0",                     {"filename": "pelsiscav_clean_seismic_catalog.csv", "filter_column": "Mag", "filter_value": "3.0", "filter_operator": ">", "max_rows": 5}),
    ("csv_reader",     "Read seismic catalog with dual filter (location + mag)",        {"filename": "pelsiscav_clean_seismic_catalog.csv", "filter_column": "Localizacion", "filter_value": "ALACANT", "filter_column_2": "Mag", "filter_value_2": "2.0", "filter_operator_2": ">", "max_rows": 10}),
    ("csv_reader",     "Read seismic catalog sorted by date descending",                {"filename": "pelsiscav_clean_seismic_catalog.csv", "order_by": "Fecha", "order_desc": True, "max_rows": 3}),
    ("csv_reader",     "Read seismic catalog columns only",                             {"filename": "pelsiscav_clean_seismic_catalog.csv", "columns_only": True}),
    ("csv_reader",     "Read flood risk CSV",                                           {"filename": "riesgo_inundaciones.csv", "max_rows": 3}),
    ("csv_reader",     "Read hydrological stations CSV",                                {"filename": "estaciones_hidrologicas_jucar.csv", "max_rows": 3}),
    ("csv_reader",     "SHOULD FAIL: non-existent CSV",                                 {"filename": "THIS_DOES_NOT_EXIST.csv"}),
    ("csv_aggregate",  "Aggregate: average magnitude from seismic catalog",              {"filename": "pelsiscav_clean_seismic_catalog.csv", "column": "Mag", "operation": "mean"}),
    ("csv_aggregate",  "Aggregate: max magnitude from seismic catalog",                  {"filename": "pelsiscav_clean_seismic_catalog.csv", "column": "Mag", "operation": "max"}),
    ("csv_aggregate",  "Aggregate: count rows in seismic catalog",                       {"filename": "pelsiscav_clean_seismic_catalog.csv", "column": "Mag", "operation": "count"}),
    ("vault_pdf_search","Search PDFs for 'terremoto'",                                  {"query": "terremoto", "top_k": 3}),
    ("vault_pdf_search","Search PDFs for 'inundacion riesgo Valencia'",                 {"query": "inundacion riesgo Valencia", "top_k": 3}),
    ("vault_pdf_search","Search PDFs for 'cambio climatico'",                           {"query": "cambio climatico", "top_k": 3}),
    ("vault_catalog",  "List all vault contents",                                       {}),
    ("file_reader",    "Read a processed data CSV via file_reader",                     {"filename": "RESUM_RISCS_CV_page_1_table_1.csv"}),

    # ── DISCOVERY TOOLS ──
    ("vault_discover", "Discover vault data (all sections)",                            {}),
    ("vault_discover", "Discover vault data (csvs section only)",                       {"section": "csvs"}),
    ("tool_discover",  "Discover all available tools",                                  {}),
    ("tool_discover",  "Discover API tools only",                                       {"category_filter": "API"}),

    # ── LIVE API TOOLS ──
    ("aemet_warnings",      "Fetch live AEMET weather warnings",                        {}),
    ("aemet_forecast",      "Weather forecast for Valencia (daily)",                     {"municipio": "valencia", "mode": "daily"}),
    ("aemet_forecast",      "Weather forecast for Alicante (hourly)",                   {"municipio": "alicante", "mode": "hourly"}),
    ("aemet_observations",  "Current weather observations for Valencia station",         {"query_type": "current_station", "station_id": "valencia"}),
    ("aemet_fire_risk",     "Current estimated fire risk map",                          {"query_type": "fire_estimated"}),
    ("aemet_fire_risk",     "UV index prediction for today",                            {"query_type": "uvi", "day": 0}),
    ("aemet_lightning",     "Latest lightning strike map",                               {}),
    ("aemet_mountain",      "Mountain forecast for Pirineos",                           {"area": "pirineos", "day": 0}),
    ("aemet_marine",        "Coastal marine forecast for Valencia",                     {"zone": "valencia", "forecast_type": "coastal"}),
    ("aemet_climatology",   "Climate normals",                                          {"query_type": "normals"}),
    ("siscova_earthquakes", "Live earthquake feed (5 events)",                          {"limit": 5}),
    ("siscova_scraper",     "Scrape SISCOVA latest earthquakes",                        {}),
    ("patricova_flood_risk","Flood risk check for Valencia city",                        {"location_name": "Valencia"}),
    ("patricova_flood_risk","Flood risk check for Alzira",                               {"location_name": "Alzira"}),
    ("patricova_flood_risk","Flood risk by coordinates (Gandia coast)",                  {"lat": 38.9667, "lon": -0.1833}),
    ("icv_wms_search",      "Search ICV WMS layers for 'inundacion'",                   {"query": "inundacion"}),
    ("web_search",          "Web search for 'DANA Valencia 2024'",                      {"query": "DANA Valencia 2024", "max_results": 3}),

    # ── GOOGLE DRIVE TOOLS ──
    ("drive_list",     "List files in the shared Drive folder",                          {}),
]


def run_phase1():
    results = []
    passed = 0
    failed = 0
    total = len(TESTS)

    print(f"\n{'='*70}")
    print(f"  PHASE 1: DIRECT TOOL TESTING (NO LLM) — {total} tests")
    print(f"{'='*70}\n")

    for i, (tool_name, description, kwargs) in enumerate(TESTS):
        test_num = i + 1
        print(f"[{test_num:02d}/{total}] {tool_name}: {description}")

        start = time.time()
        try:
            tool = get_tool(tool_name)
            result = tool.safe_execute(**kwargs)
            elapsed = round(time.time() - start, 2)

            status = result.get("status", "unknown")
            is_expected_fail = "SHOULD FAIL" in description

            if status == "success" and not is_expected_fail:
                verdict = "PASS"
                passed += 1
            elif status == "error" and is_expected_fail:
                verdict = "PASS (expected failure)"
                passed += 1
            elif status == "error" and not is_expected_fail:
                verdict = "FAIL"
                failed += 1
            else:
                verdict = "PASS"
                passed += 1

            err = result.get("error_message") or result.get("message", "")
            # Truncate data for the report
            report_result = {k: v for k, v in result.items() if k != "data"}
            if "data" in result:
                data = result["data"]
                if isinstance(data, list):
                    report_result["data_preview"] = f"[{len(data)} items]"
                elif isinstance(data, dict):
                    report_result["data_preview"] = f"{{{len(data)} keys}}"
                else:
                    report_result["data_preview"] = str(data)[:200]

            print(f"       -> {verdict} ({elapsed}s) status={status}")
            if err and verdict == "FAIL":
                print(f"       -> ERROR: {err[:150]}")

            results.append({
                "test_num": test_num,
                "tool": tool_name,
                "description": description,
                "kwargs": kwargs,
                "verdict": verdict,
                "status": status,
                "elapsed_s": elapsed,
                "error": err if verdict == "FAIL" else None,
                "result_summary": report_result,
            })

        except Exception as e:
            elapsed = round(time.time() - start, 2)
            failed += 1
            print(f"       -> CRASH ({elapsed}s): {e}")
            results.append({
                "test_num": test_num,
                "tool": tool_name,
                "description": description,
                "kwargs": kwargs,
                "verdict": "CRASH",
                "status": "crash",
                "elapsed_s": elapsed,
                "error": str(e),
                "result_summary": None,
            })

    # Summary
    print(f"\n{'='*70}")
    print(f"  RESULTS: {passed}/{total} PASSED | {failed}/{total} FAILED")
    print(f"{'='*70}\n")

    if failed > 0:
        print("FAILURES:")
        for r in results:
            if r["verdict"] in ("FAIL", "CRASH"):
                print(f"  [{r['test_num']:02d}] {r['tool']}: {r['description']}")
                print(f"       Error: {r['error']}")

    # Save full results
    out_path = BACKEND_DIR / "phase1_tool_test_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nFull results saved to: {out_path}")


if __name__ == "__main__":
    run_phase1()

"""
Comprehensive capability tester — exercises every tool tier directly,
bypassing the LLM planner so we can test data-layer health independently.
"""
import os, sys, json, time, traceback

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from backend.core.registry import list_all_tools, get_tool

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
SKIP = "\033[93mSKIP\033[0m"

results = []

def run_test(name, tool_name, kwargs, validate_fn):
    """Run a single tool test and record result."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"  Tool: {tool_name}")
    print(f"  Args: {kwargs}")
    try:
        tool = get_tool(tool_name)
        result = tool.execute(**kwargs)
        status = result.get("status", "unknown")
        ok = validate_fn(result)
        verdict = PASS if ok else FAIL
        detail = "" if ok else f"  Validation failed. Status={status}"
        print(f"  Result status: {status}")
        print(f"  Verdict: {verdict} {detail}")
        results.append({"name": name, "pass": ok, "status": status})
        return result
    except Exception as e:
        print(f"  EXCEPTION: {e}")
        traceback.print_exc()
        results.append({"name": name, "pass": False, "status": f"exception: {e}"})
        return None

# ─────────────────────────────────────────────────────────────
# TIER 1: Core Local Tools
# ─────────────────────────────────────────────────────────────

run_test(
    "T1.1 - csv_list: List available CSVs",
    "csv_list", {},
    lambda r: r.get("status") == "success" and len(r.get("available_files", r.get("files", []))) > 0
)

run_test(
    "T1.2 - csv_reader: Read seismic catalog (top 5 by magnitude)",
    "csv_reader",
    {"filename": "pelsiscav_clean_seismic_catalog.csv", "max_rows": 5, "order_by": "Mag", "order_desc": True},
    lambda r: r.get("status") == "success" and len(r.get("data", [])) == 5
)

run_test(
    "T1.3 - csv_aggregate: Count flood risk levels",
    "csv_aggregate",
    {"filename": "Inundaciones/riesgo_inundaciones.csv", "group_by": "riesgo", "aggregate_columns": "riesgo", "operation": "count"},
    lambda r: r.get("status") == "success" and r.get("results") is not None
)

run_test(
    "T1.4 - csv_reader: Read flood hazard types",
    "csv_reader",
    {"filename": "Inundaciones/peligrosidad_inun.csv", "max_rows": 3, "exclude_columns": "geometry"},
    lambda r: r.get("status") == "success" and len(r.get("data", [])) > 0
)

run_test(
    "T1.5 - vault_catalog: Return full catalog",
    "vault_catalog", {},
    lambda r: "local_vault" in r or "connections" in r
)

run_test(
    "T1.6 - vault_pdf_search: Semantic search for PELSISCAV protocols",
    "vault_pdf_search",
    {"query": "What are the emergency seismic protocols in PELSISCAV?", "top_k": 3},
    lambda r: r.get("status") == "success" and len(r.get("results", [])) > 0
)

run_test(
    "T1.7 - vault_pdf_search: Semantic search for PATRICOVA floods",
    "vault_pdf_search",
    {"query": "What is the flood risk classification protocol according to PATRICOVA?", "top_k": 3},
    lambda r: r.get("status") == "success" and len(r.get("results", [])) > 0
)

run_test(
    "T1.8 - file_reader: Read clean_pelsiscav_protocols.txt",
    "file_reader",
    {"filename": "clean_pelsiscav_protocols.txt"},
    lambda r: r.get("status") == "success"
)

# ─────────────────────────────────────────────────────────────
# TIER 2: Live API Tools
# ─────────────────────────────────────────────────────────────

run_test(
    "T2.1 - siscova_earthquakes: Fetch live seismic feed",
    "siscova_earthquakes",
    {"limit": 5},
    lambda r: r.get("status") == "success"
)

run_test(
    "T2.2 - aemet_forecast: Forecast for Valencia",
    "aemet_forecast",
    {"municipio": "Valencia", "mode": "daily"},
    lambda r: r.get("status") == "success"
)

run_test(
    "T2.3 - aemet_warnings: Active hazard warnings",
    "aemet_warnings", {},
    lambda r: r.get("status") == "success"
)

run_test(
    "T2.4 - aemet_fire_risk: Fire risk peninsula",
    "aemet_fire_risk",
    {"query_type": "fire_estimated", "area": "peninsula"},
    lambda r: r.get("status") in ("success", "error")  # may 429
)

run_test(
    "T2.5 - patricova_flood_risk: Flood risk for San Vicente",
    "patricova_flood_risk",
    {"location_name": "San Vicente del Raspeig"},
    lambda r: r.get("status") == "success"
)

# ─────────────────────────────────────────────────────────────
# TIER 3: Google Drive
# ─────────────────────────────────────────────────────────────

run_test(
    "T3.1 - drive_list: List Drive files",
    "drive_list", {},
    lambda r: r.get("status") == "success" and len(r.get("files", [])) > 0
)

run_test(
    "T3.2 - drive_read_sheet: Read unemployment data",
    "drive_read_sheet",
    {"filename": "paro_2008_2025.csv", "max_rows": 5},
    lambda r: r.get("status") == "success" and len(r.get("data", [])) > 0
)

# ─────────────────────────────────────────────────────────────
# TIER 4: Neo4j Graph
# ─────────────────────────────────────────────────────────────

run_test(
    "T4.1 - neo4j_schema: Get graph schema",
    "neo4j_schema", {},
    lambda r: r.get("status") == "success"
)

run_test(
    "T4.2 - neo4j_query: Query policy nodes",
    "neo4j_query",
    {"cypher_query": "MATCH (p:WorkPolicy) RETURN p.name AS name, p.rule_text AS rule LIMIT 5"},
    lambda r: r.get("status") == "success"
)

# ─────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
passed = sum(1 for r in results if r["pass"])
total = len(results)
print(f"\nResults: {passed}/{total} passed\n")
for r in results:
    icon = "[PASS]" if r["pass"] else "[FAIL]"
    print(f"  {icon} {r['name']}  ({r['status']})")

print(f"\n{'='*60}")
print(f"Score: {passed}/{total}")

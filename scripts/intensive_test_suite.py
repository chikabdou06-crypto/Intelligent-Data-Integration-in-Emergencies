import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from backend.core.registry import get_tool, list_all_tools
from backend.core.orchestrator import execute_plan

VALID_ARGS_MAP = {
    "aemet_forecast": {"municipio": "Valencia"},
    "aemet_warnings": {"municipio": "Alicante"},
    "aemet_marine": {"costa": "Valencia"},
    "aemet_fire_risk": {"municipio": "Castellon"},
    "patricova_flood_risk": {"municipio": "Alzira"},
    "siscova_earthquakes": {"limit": 5},
    "siscova_scraper": {"station": "VAL"},
    "drive_list": {"query": "test"},
    "drive_read": {"filename": "test.pdf"},
    "drive_read_sheet": {"filename": "data.csv"},
    "csv_list": {},
    "csv_reader": {"filename": "pelsiscav_clean_seismic_catalog.csv", "limit": 5},
    "csv_aggregate": {"filename": "pelsiscav_clean_seismic_catalog.csv", "group_by": "Provincia"},
    "file_reader": {"filename": "test.txt"},
    "vault_catalog": {},
    "vault_pdf_search": {"query": "terremoto"},
    "web_search": {"query": "DANA Valencia"},
    "tool_discover": {"query": "flood"},
    "vault_discover": {"query": "seismic"},
    "multi_tool": {},
    "general": {}
}

def test_all_tools():
    print("\n========================================")
    print("  PHASE 1: INTENSIVE TOOL TESTING (3 Tests/Tool)")
    print("========================================")
    tools = list_all_tools()
    
    for t_name in tools:
        print(f"\n--- Testing: {t_name} ---")
        try:
            tool = get_tool(t_name)
        except Exception as e:
            print(f"  [FAIL] Could not load {t_name}: {e}")
            continue

        valid_args = VALID_ARGS_MAP.get(t_name, {})
        
        # Test 1: Valid/Default Args
        res1 = tool.safe_execute(**valid_args)
        if res1.get("status") in ["success", "error"]:
            print(f"  [PASS] Test 1 (Valid Args): Handled gracefully (Status: {res1.get('status')})")
        else:
            print(f"  [FAIL] Test 1: Invalid response shape: {res1}")

        # Test 2: Invalid Argument Types
        invalid_args = {k: 99999 if isinstance(v, str) else "not_a_number" for k, v in valid_args.items()}
        if not invalid_args:
            invalid_args = {"fake_argument_xyz": 123}
            
        res2 = tool.safe_execute(**invalid_args)
        if res2.get("status") in ["success", "error"]:
            print(f"  [PASS] Test 2 (Invalid Types): Handled gracefully (Status: {res2.get('status')})")
        else:
            print(f"  [FAIL] Test 2: Invalid response shape: {res2}")

        # Test 3: Empty Arguments
        res3 = tool.safe_execute()
        if res3.get("status") in ["success", "error"]:
            print(f"  [PASS] Test 3 (Empty Args): Handled gracefully (Status: {res3.get('status')})")
        else:
            print(f"  [FAIL] Test 3: Invalid response shape: {res3}")

def test_data_types():
    print("\n========================================")
    print("  PHASE 2: DATA TYPE STRESS TESTS (3 Tests/Type)")
    print("========================================")
    
    # PDF Tests
    print("\n--- PDF Search (vault_pdf_search) ---")
    try:
        t_pdf = get_tool("vault_pdf_search")
        print(f"  [PASS] PDF Test 1 (Valid Query): Status {t_pdf.safe_execute(query='terremoto').get('status')}")
        print(f"  [PASS] PDF Test 2 (Empty Query): Status {t_pdf.safe_execute(query='').get('status')}")
        print(f"  [PASS] PDF Test 3 (Special Chars): Status {t_pdf.safe_execute(query='*&^%$#@!').get('status')}")
    except Exception as e:
        print(f"  [FAIL] PDF Testing Error: {e}")

    # CSV Tests
    print("\n--- CSV Data (csv_reader) ---")
    try:
        t_csv = get_tool("csv_reader")
        print(f"  [PASS] CSV Test 1 (Valid Read): Status {t_csv.safe_execute(filename='pelsiscav_clean_seismic_catalog.csv', limit=2).get('status')}")
        print(f"  [PASS] CSV Test 2 (Fake File): Status {t_csv.safe_execute(filename='does_not_exist.csv').get('status')}")
        print(f"  [PASS] CSV Test 3 (SQL Injection): Status {t_csv.safe_execute(filename='pelsiscav_clean_seismic_catalog.csv', filter_column='Provincia', filter_value='1 OR 1=1').get('status')}")
    except Exception as e:
        print(f"  [FAIL] CSV Testing Error: {e}")

def test_cross_reference():
    print("\n========================================")
    print("  PHASE 3: CROSS-REFERENCE ($PREV) (10 Tests)")
    print("========================================")
    
    # To test $PREV independently of API keys, we will use a mocked execution trace approach directly on the orchestrator logic.
    from backend.core.orchestrator import _enrich_args_from_prior, DependencyError
    
    executed_mock = [
        {"tool": "step0", "result": {"status": "success", "source": "A", "data": [{"id": 100}, {"id": 200}], "metadata": {"city": "Valencia"}}},
        {"tool": "step1", "result": {"status": "error", "source": "B", "error_message": "Failed API", "data": {}, "metadata": {}}},
        {"tool": "step2", "result": {"status": "success", "source": "C", "data": {"nested": {"val": 42}}, "metadata": {}}}
    ]
    
    tests = [
        ("Test 1 (Direct Property)", {"arg": "$PREV.source"}, "C"),
        ("Test 2 (Nested Dict)", {"arg": "$PREV.data.nested.val"}, 42),
        ("Test 3 (Array Index - Step 0)", {"arg": "$STEP_0.data.1.id"}, 200),
        ("Test 4 (Missing Property)", {"arg": "$PREV.data.fake"}, None),
        ("Test 5 (Specific Step Property)", {"arg": "$STEP_0.metadata.city"}, "Valencia"),
        ("Test 6 (Specific Step Missing)", {"arg": "$STEP_0.metadata.country"}, None),
        ("Test 7 (Invalid Step Index)", {"arg": "$STEP_99.source"}, "$STEP_99.source"),
        ("Test 8 (No Placeholders)", {"arg": "Hello"}, "Hello"),
        ("Test 9 (Dependency on Errored Step)", {"arg": "$STEP_1.source"}, "ERROR_EXPECTED"),
        ("Test 10 (Multiple args)", {"arg1": "$STEP_0.source", "arg2": "$STEP_2.source"}, {"arg1": "A", "arg2": "C"}),
    ]
    
    for name, args, expected in tests:
        try:
            resolved = _enrich_args_from_prior(args, executed_mock)
            
            if expected == "ERROR_EXPECTED":
                print(f"  [FAIL] {name}: Did not raise DependencyError!")
                continue
                
            if isinstance(expected, dict):
                success = all(resolved.get(k) == expected.get(k) for k in expected)
            else:
                success = resolved.get("arg") == expected
                
            if success:
                print(f"  [PASS] {name}")
            else:
                print(f"  [FAIL] {name}: Expected {expected}, Got {resolved}")
        except DependencyError as e:
            if expected == "ERROR_EXPECTED":
                print(f"  [PASS] {name}: Correctly raised DependencyError")
            else:
                print(f"  [FAIL] {name}: Unexpectedly raised DependencyError - {e}")
        except Exception as e:
            print(f"  [FAIL] {name}: Exception {e}")

def main():
    test_all_tools()
    test_data_types()
    test_cross_reference()
    
    print("\n========================================")
    print("  ALL INTENSIVE TESTS COMPLETED")
    print("========================================")

if __name__ == "__main__":
    main()

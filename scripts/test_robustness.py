import sys
import os
import json
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from backend.core.registry import get_tool
from backend.core.orchestrator import execute_plan

def test_tool_robustness(tool_name: str, valid_args: dict, invalid_args: dict):
    print(f"\n--- Testing Tool: {tool_name} ---")
    try:
        tool = get_tool(tool_name)
    except Exception as e:
        print(f"[FAIL] Failed to load tool {tool_name}: {e}")
        return

    # Test Valid Args
    print(f"  [Test] Valid Args: {valid_args}")
    result = tool.safe_execute(**valid_args)
    if result.get("status") == "success":
        print(f"    [PASS] Success (Returned {len(str(result.get('data', '')))} bytes of data)")
    else:
        print(f"    [FAIL] Unexpected Failure: {result.get('error_message')}")

    # Test Invalid Args
    print(f"  [Test] Invalid Args: {invalid_args}")
    result = tool.safe_execute(**invalid_args)
    if result.get("status") == "error":
        print(f"    [PASS] Gracefully handled error: {result.get('error_message')}")
    else:
        print(f"    [FAIL] Did not fail as expected! Returned: {result.get('status')}")

    # Test Empty Args
    print(f"  [Test] Empty Args: {{}}")
    result = tool.safe_execute()
    if result.get("status") == "error" or result.get("status") == "success":
        print(f"    [PASS] Gracefully handled empty args (Status: {result.get('status')})")
    else:
        print(f"    [FAIL] Bad response shape: {result}")

def test_cross_reference_resolution():
    print("\n--- Testing Orchestrator Cross-Reference ($PREV) ---")
    
    mock_plan = [
        {
            "tool": "aemet_forecast",
            "arguments": {"municipio": "Valencia"}
        },
        {
            "tool": "aemet_warnings",
            # We want to test if $PREV resolves correctly.
            # Assuming aemet_forecast returns data with a metadata field. We don't know the exact metadata here,
            # but we can simulate a plan that extracts from the first step.
            "arguments": {"municipio": "$PREV.source"}
        }
    ]
    
    print("  [Test] Executing Plan with $PREV...")
    executed = execute_plan(mock_plan)
    
    step1 = executed[0]
    step2 = executed[1]
    
    print(f"    Step 1 Source: {step1['result'].get('source')}")
    print(f"    Step 2 Resolved Argument 'municipio': {step2['arguments'].get('municipio')}")
    
    if step2['arguments'].get('municipio') == step1['result'].get('source'):
        print("    [PASS] Cross-reference ($PREV) successfully resolved!")
    else:
        print("    [FAIL] Cross-reference resolution failed!")

def main():
    print("========================================")
    print("  AGENT ROBUSTNESS TEST SUITE")
    print("========================================")
    
    test_tool_robustness(
        tool_name="aemet_forecast", 
        valid_args={"municipio": "Valencia"}, 
        invalid_args={"municipio": "FakeCityXYZ"}
    )
    
    test_tool_robustness(
        tool_name="siscova_earthquakes", 
        valid_args={"limit": 5}, 
        invalid_args={"limit": "not_an_int"}
    )
    
    test_tool_robustness(
        tool_name="patricova_flood_risk", 
        valid_args={"municipio": "Alicante"}, 
        invalid_args={"municipio": ""}
    )
    
    test_cross_reference_resolution()
    
    print("\n========================================")
    print("  TESTING COMPLETE")
    print("========================================")

if __name__ == "__main__":
    main()

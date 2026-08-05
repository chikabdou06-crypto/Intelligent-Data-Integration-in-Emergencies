import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from backend.tools.local.file_reader import FileReaderTool

def main():
    print("=" * 60)
    print("Testing Universal File Reader Tool")
    print("=" * 60)

    tool = FileReaderTool()

    # 1. Test Text File
    print("\n[Test 1] Reading sample_test.txt...")
    res_txt = tool.execute(filename="sample_test.txt")
    print(f"Status: {res_txt.get('status')}")
    print(f"File Type: {res_txt.get('file_type')}")
    print(f"Length: {res_txt.get('length')} chars")
    print(f"Content:\n{res_txt.get('content')}")

    # 2. Test JSON File
    print("\n[Test 2] Reading sample_test.json...")
    res_json = tool.execute(filename="sample_test.json")
    print(f"Status: {res_json.get('status')}")
    print(f"File Type: {res_json.get('file_type')}")
    print(f"Data parsed successfully: {'data' in res_json}")
    print(f"Project Name: {res_json.get('data', {}).get('project_name')}")

    # 3. Test Security Boundary (Path Traversal)
    print("\n[Test 3] TESTING SECURITY BOUNDARY: Attempting path traversal (filename='../../credentials.json')...")
    res_sec = tool.execute(filename="../../credentials.json")
    print(f"Status: {res_sec.get('status')}")
    print(f"Message: {res_sec.get('message')}")

if __name__ == "__main__":
    main()

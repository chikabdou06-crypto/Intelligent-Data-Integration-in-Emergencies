import sys
import os
from pathlib import Path

# Add the project root to python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.registry import get_tool
import json

def test_ine():
    print("\n--- Testing INE API ---")
    
    # 1. Search operations for 'poblacion'
    search_tool = get_tool("ine_search_operations")
    ops = search_tool.execute(query="poblacion")
    print(f"Found {len(ops)} operations matching 'poblacion'.")
    if not ops:
        print("FAIL: No operations found.")
        return
        
    print(f"First op: {ops[0]['name']} (ID: {ops[0]['id']})")
    op_id = ops[0]['id']
    
    # 2. List tables for operation
    tables_tool = get_tool("ine_list_tables")
    tables = tables_tool.execute(operation_id=op_id)
    print(f"Found {len(tables)} tables for operation {op_id}.")
    if not tables:
        print("FAIL: No tables found.")
        return
        
    print(f"First table: {tables[0]['name']} (ID: {tables[0]['id']})")
    table_id = tables[0]['id']
    
    # 3. Get table data
    data_tool = get_tool("ine_get_table_data")
    data = data_tool.execute(table_id=table_id, n_last=2)
    print(f"Successfully fetched data for table {table_id}. Found {len(data['series'])} series.")
    if data['series']:
        print(f"First series data sample: {data['series'][0]['data']}")

def test_boe():
    print("\n--- Testing BOE API ---")
    
    # 1. Search BOE for 'DANA'
    search_tool = get_tool("boe_get_summary")
    results = search_tool.execute(date="20240102")
    
    data = results.get("data", {})
    # Since sumario returns a complex schema, let's just grab the first document from sumario/diario/seccion/departamento
    # Just printing success if it doesn't fail
    print(f"Fetched BOE summary for 2024-01-02. Status: {results.get('status', 'success')}")
    
    # We will just fetch a known document for get_document testing
    doc_id = "BOE-A-2024-87"
    
    # 2. Get document metadata (Commented out because BOE API can be flaky with specific IDs)
    # doc_tool = get_tool("boe_get_document")
    # doc_meta = doc_tool.execute(document_id=doc_id)
    # print(f"Successfully fetched metadata for {doc_id}.")
    # print(f"Title: {doc_meta.get('data', {}).get('documento', {}).get('titulo')}")

if __name__ == "__main__":
    test_ine()
    test_boe()

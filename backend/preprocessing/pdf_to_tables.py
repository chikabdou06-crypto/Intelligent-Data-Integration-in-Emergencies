import os
import sys
import pdfplumber
import pandas as pd

# Fix paths to allow importing from backend.core
PREPROC_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(PREPROC_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from backend.core.vault_paths import VAULT_PDFS, VAULT_PROCESSED_DATA, ensure_vault_dirs

def extract_tables_from_pdf(filename: str):
    ensure_vault_dirs()
    pdf_path = os.path.join(VAULT_PDFS, filename)
    
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found.")
        return

    print(f"Processing: {filename}")
    
    # Use the base filename for output CSVs
    base_name = os.path.splitext(filename)[0].replace(" ", "_")
    
    csv_count = 0
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            
            for table_index, table in enumerate(tables, start=1):
                # Convert to pandas DataFrame
                # Often the first row is headers
                if len(table) > 1:
                    df = pd.DataFrame(table[1:], columns=table[0])
                else:
                    # In case of single-row table or weird formatting
                    df = pd.DataFrame(table)
                    
                # Clean up empty strings or newlines
                df = df.replace(r'\n', ' ', regex=True)
                
                # Create a unique output file name
                out_filename = f"{base_name}_page_{page_num}_table_{table_index}.csv"
                out_path = os.path.join(VAULT_PROCESSED_DATA, out_filename)
                
                # Export to CSV
                df.to_csv(out_path, index=False, encoding='utf-8-sig')
                print(f"  -> Extracted table to: {out_filename}")
                csv_count += 1
                
    print(f"Finished processing {filename}. Extracted {csv_count} table(s).")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_tables.py <pdf_filename>")
        print("Note: The PDF must be located in backend/vault/pdfs/")
    else:
        extract_tables_from_pdf(sys.argv[1])

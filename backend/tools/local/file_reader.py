import os
import json
from typing import Any, Dict
from backend.core.base_tool import BaseTool
from backend.core.registry import register_tool
from backend.core.vault_paths import VAULT_DIR

# Reuse CSV reader functionality for consistency
from backend.tools.local.csv_reader import read_csv_data

# Huge geometry columns stripping to save token budget
GEOMETRY_COLUMNS = {"geometry", "geom", "wkt", "geojson", "the_geom", "shape"}

def _resolve_file_path(filename: str) -> str | None:
    """Securely resolves a filename relative to the vault directory to prevent path traversal."""
    abs_vault = os.path.abspath(VAULT_DIR)
    # Try direct path first
    file_path = os.path.abspath(os.path.join(abs_vault, filename))
    if not file_path.startswith(abs_vault):
        return None
    if os.path.exists(file_path):
        return file_path
    # Search subdirectories (pdfs/, csvs/, etc.) by basename
    basename = os.path.basename(filename)
    for root, _, files in os.walk(abs_vault):
        if basename in files:
            found = os.path.abspath(os.path.join(root, basename))
            if found.startswith(abs_vault):
                return found
    return None

@register_tool(name="file_reader", category="DATA")
class FileReaderTool(BaseTool):
    name = "file_reader"
    description = "Reads, extracts, and parses local files (CSV, PDF, TXT, JSON, MD, Excel XLSX) from the vault into clean structured format."
    category = "DATA"

    def execute(
        self,
        filename: str,
        sheet_name: str = None,
        filter_column: str = None,
        filter_value: str = None,
        max_rows: int = 500,
        order_by: str = None,
        order_desc: bool = False
    ) -> Dict[str, Any]:
        file_path = _resolve_file_path(filename)
        if not file_path:
            return {"status": "error", "message": f"File '{filename}' not found in vault or access is restricted."}

        ext = os.path.splitext(filename)[1].lower()

        # ── 1. CSV Files ──
        if ext == ".csv":
            # Delegate to existing robust CSV reading logic
            # Extract just the basename as read_csv_data resolves paths inside csvs/ and data/
            csv_fn = os.path.basename(filename)
            return read_csv_data(
                filename=csv_fn,
                filter_column=filter_column,
                filter_value=filter_value,
                max_rows=max_rows,
                order_by=order_by,
                order_desc=order_desc
            )

        # ── 2. Excel Files (.xlsx, .xls) ──
        elif ext in (".xlsx", ".xls"):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(file_path, data_only=True)
                sheets = wb.sheetnames
                if not sheets:
                    return {"status": "error", "message": f"No sheets found in Excel file '{filename}'."}
                
                if not sheet_name:
                    sheet_name = sheets[0]
                elif sheet_name not in sheets:
                    return {"status": "error", "message": f"Sheet '{sheet_name}' not found. Available: {sheets}."}

                sheet = wb[sheet_name]
                rows_data = list(sheet.iter_rows(values_only=True))
                if not rows_data:
                    return {"status": "success", "sheet_name": sheet_name, "data": [], "total_rows": 0}

                # Extract headers
                headers = [str(h).strip() for h in rows_data[0] if h is not None]
                
                rows = []
                total_matched = 0
                cap = max(1, int(max_rows)) if max_rows else 500

                for r in rows_data[1:]:
                    # Skip empty rows
                    if all(cell is None for cell in r):
                        continue
                    
                    # Pad values to match headers length
                    padded_r = list(r) + [""] * (len(headers) - len(r))
                    row_dict = dict(zip(headers, padded_r))
                    
                    # Clean dictionary values
                    cleaned_dict = {str(k): (str(v).strip() if v is not None else "") for k, v in row_dict.items()}
                    
                    # Strip geometry columns to save token budget
                    clean_row = {k: v for k, v in cleaned_dict.items() if k.lower() not in GEOMETRY_COLUMNS}

                    # Filter column & value matching
                    if filter_column and filter_value:
                        val = str(clean_row.get(filter_column, "")).strip().lower()
                        target = str(filter_value).strip().lower()
                        if target not in val:
                            continue

                    total_matched += 1
                    
                    if order_by:
                        rows.append(clean_row)
                    elif len(rows) < cap:
                        rows.append(clean_row)

                # Apply sorting if order_by is specified
                if order_by:
                    def sort_key(r):
                        val = r.get(order_by, "")
                        try:
                            return float(str(val).replace(",", ""))
                        except (ValueError, TypeError):
                            return str(val)
                    rows.sort(key=sort_key, reverse=order_desc)

                truncated = len(rows) > cap
                if truncated:
                    rows = rows[:cap]

                res = {
                    "status": "success",
                    "filename": filename,
                    "sheet_name": sheet_name,
                    "headers": headers,
                    "total_rows": total_matched,
                    "returned_rows": len(rows),
                    "data": rows
                }
                if truncated:
                    res["truncated"] = True
                    res["max_rows"] = cap
                    res["message"] = f"Excel rows capped at {cap}. Apply filters to narrow results."
                return res

            except Exception as e:
                return {"status": "error", "message": f"Failed to parse Excel file: {str(e)}"}

        # ── 3. Plain Text / Markdown Files ──
        elif ext in (".txt", ".md"):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                
                max_chars = 12000
                truncated = len(text) > max_chars
                preview = text[:max_chars]
                
                res = {
                    "status": "success",
                    "filename": filename,
                    "file_type": "text",
                    "length": len(text),
                    "content": preview
                }
                if truncated:
                    res["truncated"] = True
                    res["message"] = f"File text truncated to first {max_chars} characters to fit within system limits."
                return res
            except Exception as e:
                return {"status": "error", "message": f"Failed to read text file: {str(e)}"}

        # ── 4. PDF Files ──
        elif ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                pages_text = []
                for p_num, page in enumerate(reader.pages):
                    p_text = page.extract_text() or ""
                    if p_text.strip():
                        pages_text.append(f"--- Page {p_num + 1} ---\n{p_text}")
                
                full_text = "\n\n".join(pages_text)
                
                max_chars = 15000
                truncated = len(full_text) > max_chars
                preview = full_text[:max_chars]
                
                res = {
                    "status": "success",
                    "filename": filename,
                    "file_type": "pdf",
                    "total_pages": len(reader.pages),
                    "length": len(full_text),
                    "content": preview
                }
                if truncated:
                    res["truncated"] = True
                    res["message"] = f"PDF text content truncated to first {max_chars} characters."
                return res
            except Exception as e:
                return {"status": "error", "message": f"Failed to extract PDF text: {str(e)}"}

        # ── 5. JSON Files ──
        elif ext == ".json":
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    data = json.load(f)
                return {
                    "status": "success",
                    "filename": filename,
                    "file_type": "json",
                    "data": data
                }
            except Exception as e:
                return {"status": "error", "message": f"Failed to parse JSON file: {str(e)}"}

        else:
            return {"status": "error", "message": f"Unsupported file format '{ext}'."}

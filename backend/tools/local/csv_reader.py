import os
import csv
import sys

# ── Handle CSVs with very large fields (geometry WKT/GeoJSON blobs) ──
csv.field_size_limit(2**31 - 1)

DEFAULT_MAX_ROWS = 500

# Columns that are typically huge geometry blobs — auto-excluded from row data
GEOMETRY_COLUMNS = {"geometry", "geom", "wkt", "geojson", "the_geom", "shape"}

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from backend.core.vault_paths import VAULT_CSVS, VAULT_PROCESSED_DATA, LEGACY_DATA


def get_csv_folder_paths() -> list[str]:
    return [VAULT_CSVS, VAULT_PROCESSED_DATA, LEGACY_DATA]


def get_csv_folder_path() -> str:
    """Primary CSV vault folder."""
    return VAULT_CSVS


def list_available_csvs() -> dict:
    csv_schemas = {}
    scanned = []
    for folder_path in get_csv_folder_paths():
        if not os.path.exists(folder_path):
            continue
        scanned.append(folder_path)
        for root, _, files in os.walk(folder_path):
            if any(exclude_dir in root for exclude_dir in ("CHJ_OpenData", "Sismicidad_Historica", "RESUM_RISCS")):
                continue
            for filename in files:
                if not filename.endswith(".csv"):
                    continue
                # Store relative path so _resolve_csv_path can find it or we can just use the filename if unique
                # but let's key it by the relative path to be safe, or just the basename if we want to preserve the old API.
                # Actually, the old API used filename as the key. Let's keep it as filename for now.
                if filename in csv_schemas:
                    continue
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, mode="r", encoding="utf-8-sig") as f:
                        reader = csv.reader(f)
                        headers = next(reader, None)
                        if headers:
                            headers = [h.strip() for h in headers]
                            csv_schemas[filename] = {
                                "columns": headers,
                                "file_size_bytes": os.path.getsize(file_path),
                                "folder": root,
                            }
                except Exception as e:
                    csv_schemas[filename] = {"columns": [], "error": str(e)}

    if not csv_schemas:
        return {"status": "error", "message": f"No CSV files in vault. Checked: {scanned}"}

    return {
        "status": "success",
        "csv_directories": scanned,
        "available_files": csv_schemas,
    }


def _resolve_csv_path(filename: str) -> tuple[str | None, str | None]:
    norm_filename = filename.replace("\\", "/").strip()
    basename = os.path.basename(norm_filename)
    
    for folder_path in get_csv_folder_paths():
        if not os.path.exists(folder_path):
            continue
        for root, _, files in os.walk(folder_path):
            if basename in files:
                full_path = os.path.join(root, basename)
                norm_full = full_path.replace("\\", "/")
                if norm_filename in norm_full:
                    return root, full_path
    return None, None


def _strip_geometry(row: dict, exclude_cols: set | None = None) -> dict:
    """Remove large geometry columns from a row dict to save token space."""
    skip = GEOMETRY_COLUMNS | (exclude_cols or set())
    return {k: v for k, v in row.items() if k.lower() not in skip}


def read_csv_data(
    filename: str,
    filter_column: str = None,
    filter_value: str = None,
    filter_operator: str = "contains",
    filter_column_2: str = None,
    filter_value_2: str = None,
    filter_operator_2: str = "contains",
    max_rows: int = DEFAULT_MAX_ROWS,
    columns_only: bool = False,
    exclude_columns: str = None,
    order_by: str = None,
    order_desc: bool = False,
) -> dict:
    folder_path, file_path = _resolve_csv_path(filename)
    if not file_path:
        return {"status": "error", "message": f"CSV file '{filename}' not found in vault."}

    # Parse user-specified columns to exclude (comma-separated)
    extra_exclude = set()
    if exclude_columns:
        extra_exclude = {c.strip().lower() for c in exclude_columns.split(",")}

    try:
        rows = []
        headers = []
        total_matched = 0

        with open(file_path, mode="r", encoding="utf-8-sig") as f:
            reader_obj = csv.reader(f)
            raw_headers = next(reader_obj, None)
            if raw_headers:
                headers = [h.strip() for h in raw_headers]
            reader = csv.DictReader(f, fieldnames=headers)

            if columns_only:
                return {
                    "status": "success",
                    "filename": filename,
                    "headers": headers,
                    "columns_only": True,
                    "total_rows": None,
                    "data": [],
                }

            cap = max(1, int(max_rows)) if max_rows else DEFAULT_MAX_ROWS

            for row in reader:
                # Helper to evaluate a filter
                def check_filter(f_col, f_val, f_op):
                    if not f_col or f_val is None: return True
                    # Case-insensitive column search
                    actual_col = None
                    for k in row.keys():
                        if k and k.lower() == f_col.lower():
                            actual_col = k
                            break
                    if not actual_col: return False # Column not found, filter fails
                    
                    col_val = row.get(actual_col, "")
                    op = f_op.strip() if f_op else "contains"
                    if op == "contains":
                        if str(f_val).strip().lower() not in str(col_val).strip().lower():
                            return False
                    elif op == "==" or op == "=":
                        if str(f_val).strip().lower() != str(col_val).strip().lower():
                            return False
                    elif op in (">", ">=", "<", "<="):
                        try:
                            val_f = float(str(col_val).replace(",", ""))
                            tgt_f = float(str(f_val).replace(",", ""))
                            if op == ">" and not (val_f > tgt_f): return False
                            if op == ">=" and not (val_f >= tgt_f): return False
                            if op == "<" and not (val_f < tgt_f): return False
                            if op == "<=" and not (val_f <= tgt_f): return False
                        except (ValueError, TypeError):
                            return False
                    return True

                if not check_filter(filter_column, filter_value, filter_operator):
                    continue
                if not check_filter(filter_column_2, filter_value_2, filter_operator_2):
                    continue
                    
                total_matched += 1
                
                # If we are sorting, we must collect all matching rows first before capping
                if order_by:
                    rows.append(_strip_geometry(dict(row), extra_exclude))
                elif len(rows) < cap:
                    rows.append(_strip_geometry(dict(row), extra_exclude))

        if order_by:
            num_group = 1 if order_desc else 0
            str_group = 0 if order_desc else 1
            def sort_key(r):
                val = r.get(order_by, "")
                # Try numeric sort first. Dynamically group to prevent mixed-type errors and ensure valid numbers float to top.
                try:
                    return (num_group, float(str(val).replace(",", "")))
                except (ValueError, TypeError):
                    return (str_group, str(val))
                    
            rows.sort(key=sort_key, reverse=order_desc)
            
        truncated = len(rows) > cap
        if truncated:
            rows = rows[:cap]

        result = {
            "status": "success",
            "filename": filename,
            "headers": headers,
            "total_rows": total_matched,
            "returned_rows": len(rows),
            "data": rows,
        }
        if truncated:
            result["truncated"] = True
            result["max_rows"] = cap
            result["message"] = f"Results capped at {cap} rows. Refine filters for more precision."
        return result
    except Exception as e:
        return {"status": "error", "message": f"Failed to read CSV: {str(e)}"}


# ────────────────────────────────────────────────────────────────
#  NEW: Server-side aggregation tool — processes ALL rows
# ────────────────────────────────────────────────────────────────

def csv_aggregate(
    filename: str,
    aggregate_columns: str | list,
    operation: str = "sum",
    filter_column: str = None,
    filter_value: str = None,
    group_by: str | list = None,
    filters: list = None,
    **kwargs
) -> dict:
    """
    Perform a server-side aggregation (sum, count, avg, min, max) over ALL rows
    of a CSV file, optionally filtered and grouped. This avoids the row-cap
    limitation of csv_reader.
    """
    folder_path, file_path = _resolve_csv_path(filename)
    if not file_path:
        return {"status": "error", "message": f"CSV file '{filename}' not found in vault."}

    op = operation.strip().lower()
    if op not in ("sum", "count", "avg", "min", "max"):
        return {"status": "error", "message": f"Unsupported operation '{operation}'. Use sum, count, avg, min, or max."}

    if isinstance(aggregate_columns, (list, tuple)):
        agg_cols = [str(c).strip() for c in aggregate_columns]
    else:
        agg_cols = [c.strip() for c in str(aggregate_columns).split(",") if c.strip()]

    group_cols = []
    if group_by:
        if isinstance(group_by, (list, tuple)):
            group_cols = [str(g).strip() for g in group_by]
        else:
            group_cols = [g.strip() for g in str(group_by).split(",") if g.strip()]

    # Check for dict/list filters
    all_filters = []
    if filter_column and filter_value:
        all_filters.append((str(filter_column), str(filter_value)))
    if filters and isinstance(filters, list):
        for f in filters:
            if isinstance(f, dict) and f.get("column") and "value" in f:
                all_filters.append((str(f["column"]), str(f["value"])))

    try:
        # accumulators: {group_key: {col: [values]}}
        groups: dict[str, dict[str, list[float]]] = {}
        total_rows = 0
        skipped = 0

        with open(file_path, mode="r", encoding="utf-8-sig") as f:
            reader_obj = csv.reader(f)
            raw_headers = next(reader_obj, None)
            if raw_headers:
                headers = [h.strip() for h in raw_headers]
            reader = csv.DictReader(f, fieldnames=headers)

            # Validate requested columns exist
            missing = [c for c in agg_cols if c not in headers]
            if missing:
                return {
                    "status": "error",
                    "message": f"Column(s) {missing} not found. Available: {headers}",
                }

            for row in reader:
                # Apply filter
                match = True
                for col_name, val_str in all_filters:
                    col_val = row.get(col_name, "")
                    if val_str.strip().lower() not in col_val.strip().lower():
                        match = False
                        break
                if not match:
                    continue

                total_rows += 1
                if group_cols:
                    grp_key = " | ".join(str(row.get(g, "")).strip() for g in group_cols)
                else:
                    grp_key = "__ALL__"

                if grp_key not in groups:
                    groups[grp_key] = {c: [] for c in agg_cols}

                for c in agg_cols:
                    raw = row.get(c, "").strip().replace(",", "")
                    try:
                        groups[grp_key][c].append(float(raw))
                    except (ValueError, TypeError):
                        skipped += 1

        # Compute results
        results = {}
        for grp_key, cols_data in groups.items():
            agg_result = {}
            for c, vals in cols_data.items():
                if not vals:
                    agg_result[c] = None
                    continue
                if op == "sum":
                    agg_result[c] = round(sum(vals), 4)
                elif op == "count":
                    agg_result[c] = len(vals)
                elif op == "avg":
                    agg_result[c] = round(sum(vals) / len(vals), 4)
                elif op == "min":
                    agg_result[c] = min(vals)
                elif op == "max":
                    agg_result[c] = max(vals)
            results[grp_key] = agg_result

        return {
            "status": "success",
            "filename": filename,
            "operation": op,
            "aggregate_columns": agg_cols,
            "group_by": group_by,
            "total_rows_processed": total_rows,
            "non_numeric_skipped": skipped,
            "results": results,
        }

    except Exception as e:
        return {"status": "error", "message": f"Aggregation failed: {str(e)}"}


from backend.core.base_tool import BaseTool
from backend.core.registry import register_tool

@register_tool(name="csv_list", category="DATA")
class CsvListTool(BaseTool):
    name = "csv_list"
    description = "Lists all CSV files in the vault with column headers (schemas only, no row data)."
    category = "DATA"

    def execute(self) -> dict:
        return list_available_csvs()

@register_tool(name="csv_reader", category="DATA")
class CsvReaderTool(BaseTool):
    name = "csv_reader"
    description = "Reads and filters rows from a specific CSV file. Geometry columns are auto-excluded."
    category = "DATA"

    def execute(
        self,
        filename: str,
        filter_column: str = None,
        filter_value: str = None,
        filter_operator: str = "contains",
        filter_column_2: str = None,
        filter_value_2: str = None,
        filter_operator_2: str = "contains",
        max_rows: int = DEFAULT_MAX_ROWS,
        columns_only: bool = False,
        exclude_columns: str = None,
        order_by: str = None,
        order_desc: bool = False
    ) -> dict:
        return read_csv_data(filename, filter_column, filter_value, filter_operator, filter_column_2, filter_value_2, filter_operator_2, max_rows, columns_only, exclude_columns, order_by, order_desc)

@register_tool(name="csv_aggregate", category="DATA")
class CsvAggregateTool(BaseTool):
    name = "csv_aggregate"
    description = "Performs server-side aggregation (sum, count, avg, min, max) across ALL rows of a CSV file."
    category = "DATA"

    def execute(
        self,
        filename: str,
        aggregate_columns: str | list,
        operation: str = "sum",
        filter_column: str = None,
        filter_value: str = None,
        group_by: str | list = None,
        filters: list = None
    ) -> dict:
        return csv_aggregate(filename, aggregate_columns, operation, filter_column, filter_value, group_by, filters=filters)



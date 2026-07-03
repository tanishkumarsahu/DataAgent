"""data_handler.py — File loading, profiling, and automated cleaning pipeline.

Responsibilities:
- load_file: parse CSV / XLSX bytes into a pandas DataFrame
- profile_dataframe: produce a JSON-serialisable summary
- auto_clean: apply deterministic cleaning steps and return a report
"""

from __future__ import annotations

import io
import os
from typing import Any

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Parse uploaded file bytes into a DataFrame.

    Supports .csv and .xlsx / .xls formats only.
    """
    suffix = os.path.splitext(filename)[1].lower()
    stream = io.BytesIO(file_bytes)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(stream, engine="openpyxl")
    return pd.read_csv(stream)


# ---------------------------------------------------------------------------
# Profiling
# ---------------------------------------------------------------------------

def profile_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    """Return a JSON-serialisable profile dict for the given DataFrame."""

    n_rows, n_cols = df.shape
    missing_total = int(df.isna().sum().sum())
    memory_kb = round(df.memory_usage(deep=True).sum() / 1024, 2)

    columns: list[dict] = []
    for col in df.columns:
        series = df[col]
        null_count = int(series.isna().sum())
        dtype_str = str(series.dtype)
        col_info: dict[str, Any] = {
            "name": col,
            "dtype": dtype_str,
            "null_count": null_count,
            "null_pct": round(null_count / n_rows * 100, 2) if n_rows else 0,
            "unique": int(series.nunique()),
        }
        if pd.api.types.is_numeric_dtype(series):
            col_info.update(
                {
                    "mean": _safe_float(series.mean()),
                    "std": _safe_float(series.std()),
                    "min": _safe_float(series.min()),
                    "max": _safe_float(series.max()),
                    "median": _safe_float(series.median()),
                }
            )
        else:
            top = series.mode()
            col_info["top_value"] = str(top.iloc[0]) if not top.empty else None
        columns.append(col_info)

    # First 30 rows as a list-of-dicts (JSON-safe)
    preview = _df_to_json_records(df.head(30))

    return {
        "rows": n_rows,
        "cols": n_cols,
        "missing_total": missing_total,
        "memory_kb": memory_kb,
        "columns": columns,
        "preview": preview,
    }


# ---------------------------------------------------------------------------
# Automated cleaning
# ---------------------------------------------------------------------------

def auto_clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Apply a deterministic cleaning pipeline.

    Steps (in order):
    1. Drop fully-duplicate rows
    2. Strip leading/trailing whitespace from string columns
    3. Fill numeric NaNs with column median
    4. Fill categorical NaNs with column mode
    5. Flag outliers via IQR (1.5×IQR rule) — rows kept, column added

    Returns:
        cleaned_df: the cleaned DataFrame
        report: dict describing every action taken
    """

    cleaned = df.copy()
    report: dict[str, Any] = {
        "steps": [],
        "rows_before": len(df),
        "cols_before": len(df.columns),
    }

    # 1. Duplicate rows
    dup_mask = cleaned.duplicated()
    n_dups = int(dup_mask.sum())
    if n_dups:
        cleaned = cleaned[~dup_mask].reset_index(drop=True)
        report["steps"].append(
            {"action": "remove_duplicates", "detail": f"Removed {n_dups} duplicate row(s)."}
        )

    # 2. Strip whitespace
    str_cols = cleaned.select_dtypes(include="object").columns.tolist()
    stripped_cols: list[str] = []
    for col in str_cols:
        before = cleaned[col].copy()
        cleaned[col] = cleaned[col].str.strip()
        if not cleaned[col].equals(before):
            stripped_cols.append(col)
    if stripped_cols:
        report["steps"].append(
            {
                "action": "strip_whitespace",
                "detail": f"Stripped whitespace in {len(stripped_cols)} column(s): {', '.join(stripped_cols)}.",
            }
        )

    # 3. Fill numeric NaNs with median
    num_cols = cleaned.select_dtypes(include=np.number).columns.tolist()
    filled_num: list[str] = []
    for col in num_cols:
        n_null = int(cleaned[col].isna().sum())
        if n_null:
            median_val = cleaned[col].median()
            cleaned[col] = cleaned[col].fillna(median_val)
            filled_num.append(f"{col} ({n_null} cells → median {_safe_float(median_val)})")
    if filled_num:
        report["steps"].append(
            {
                "action": "fill_numeric_nulls",
                "detail": f"Filled numeric NaNs with median: {'; '.join(filled_num)}.",
            }
        )

    # 4. Fill categorical NaNs with mode
    filled_cat: list[str] = []
    for col in str_cols:
        n_null = int(cleaned[col].isna().sum())
        if n_null:
            mode_vals = cleaned[col].mode()
            if not mode_vals.empty:
                mode_val = mode_vals.iloc[0]
                cleaned[col] = cleaned[col].fillna(mode_val)
                filled_cat.append(f"{col} ({n_null} cells → '{mode_val}')")
    if filled_cat:
        report["steps"].append(
            {
                "action": "fill_categorical_nulls",
                "detail": f"Filled categorical NaNs with mode: {'; '.join(filled_cat)}.",
            }
        )

    # 5. Outlier flagging (IQR)
    outlier_flags: list[str] = []
    for col in num_cols:
        q1 = cleaned[col].quantile(0.25)
        q3 = cleaned[col].quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        flag_col = f"_outlier_{col}"
        cleaned[flag_col] = ((cleaned[col] < lower) | (cleaned[col] > upper)).astype(int)
        n_out = int(cleaned[flag_col].sum())
        if n_out:
            outlier_flags.append(f"{col}: {n_out} outlier(s) (IQR method)")
    if outlier_flags:
        report["steps"].append(
            {
                "action": "flag_outliers",
                "detail": f"Flagged outliers (new _outlier_* columns): {'; '.join(outlier_flags)}.",
            }
        )

    report["rows_after"] = len(cleaned)
    report["cols_after"] = len(cleaned.columns)

    if not report["steps"]:
        report["steps"].append(
            {"action": "no_issues", "detail": "Dataset looks clean — no issues were found."}
        )

    return cleaned, report


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Serialise a DataFrame to UTF-8 CSV bytes."""
    return df.to_csv(index=False).encode("utf-8")


def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Serialise a DataFrame to Excel (.xlsx) bytes."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(value) -> float | None:
    try:
        v = float(value)
        return round(v, 4) if np.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _df_to_json_records(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to a list of plain Python dicts (JSON-safe)."""
    records = []
    for row in df.itertuples(index=False):
        rec: dict[str, Any] = {}
        for col, val in zip(df.columns, row):
            if isinstance(val, float) and not np.isfinite(val):
                rec[col] = None
            elif hasattr(val, "item"):  # numpy scalar
                rec[col] = val.item()
            elif isinstance(val, (np.integer, np.floating)):
                rec[col] = val.item()
            elif not isinstance(val, (list, dict)) and pd.isna(val):
                rec[col] = None
            else:
                rec[col] = str(val) if not isinstance(val, (int, float, bool, type(None), str)) else val
        records.append(rec)
    return records

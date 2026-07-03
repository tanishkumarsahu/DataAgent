"""chart_builder.py — Build matplotlib/seaborn charts and return PNG bytes."""

from __future__ import annotations

import io
from typing import Any

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

_DARK_BG = "#0f0f1a"
_CARD_BG = "#1a1a2e"
_TEXT    = "#e2e8f0"
_ACCENT  = "#7c3aed"
_GRID    = "#2d2d4e"
_PALETTE = ["#7c3aed", "#06b6d4", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6"]


def _apply_dark_style(fig: plt.Figure, ax: plt.Axes) -> None:
    fig.patch.set_facecolor(_DARK_BG)
    ax.set_facecolor(_CARD_BG)
    ax.tick_params(colors=_TEXT, labelsize=9)
    ax.xaxis.label.set_color(_TEXT)
    ax.yaxis.label.set_color(_TEXT)
    ax.title.set_color(_TEXT)
    for spine in ax.spines.values():
        spine.set_edgecolor(_GRID)
    ax.grid(color=_GRID, linestyle="--", linewidth=0.5, alpha=0.6)


def validate_chart_spec(
    df: pd.DataFrame,
    chart_type: str,
    x_column: str = "",
    y_column: str = "",
) -> str | None:
    """Check if a chart can be rendered. Returns None if OK, or an error message string."""
    valid_types = {"line", "bar", "scatter", "hist", "box", "heatmap"}
    if chart_type not in valid_types:
        return f"Unsupported chart type '{chart_type}'. Choose from: {', '.join(sorted(valid_types))}."

    if chart_type == "heatmap":
        num_cols = df.select_dtypes(include=np.number).columns
        num_cols = [c for c in num_cols if not c.startswith("_outlier_")]
        if len(num_cols) < 2:
            return "Heatmap requires at least 2 numeric columns in the dataset."
        return None

    if chart_type == "hist":
        target = x_column or y_column
        if not target:
            return "Histogram requires an X or Y column to be selected."
        if target not in df.columns:
            return f"Column '{target}' not found in the dataset."
        if not pd.api.types.is_numeric_dtype(df[target]):
            return f"Column '{target}' must be numeric for a histogram."
        return None

    if not x_column:
        return f"'{chart_type}' chart requires an X-axis column."
    if not y_column:
        return f"'{chart_type}' chart requires a Y-axis column."
    if x_column not in df.columns:
        return f"X-axis column '{x_column}' not found in the dataset."
    if y_column not in df.columns:
        return f"Y-axis column '{y_column}' not found in the dataset."

    if chart_type in {"line", "scatter"}:
        if not pd.api.types.is_numeric_dtype(df[y_column]):
            return f"Y-axis column '{y_column}' must be numeric for a {chart_type} chart."

    return None


def build_chart_from_params(
    df: pd.DataFrame,
    chart_type: str,
    x_column: str = "",
    y_column: str = "",
    hue_column: str = "",
    title: str = "",
) -> bytes | None:
    """Build a chart from individual parameters (no AI involved)."""
    spec = {
        "chart_type": chart_type,
        "x": x_column,
        "y": y_column,
        "hue": hue_column,
        "title": title or f"{chart_type.title()} Chart",
    }
    return build_chart_png(spec, df)


def build_chart_png(spec: dict[str, Any], df: pd.DataFrame) -> bytes | None:
    """Convert a chart spec dict + DataFrame into PNG bytes."""

    chart_type = str(spec.get("chart_type", "")).lower().strip()
    x     = str(spec.get("x",   "")).strip()
    y     = str(spec.get("y",   "")).strip()
    hue   = str(spec.get("hue", "")).strip()
    title = str(spec.get("title", "")).strip() or "Data Visualisation"

    if chart_type != "heatmap":
        if x and x not in df.columns: x = ""
        if y and y not in df.columns: y = ""
    if hue and hue not in df.columns:
        hue = ""

    if chart_type not in {"line", "bar", "scatter", "hist", "box", "heatmap"}:
        return None

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=120)
    _apply_dark_style(fig, ax)

    hue_val = hue or None
    kwargs = {}
    if hue_val:
        kwargs["palette"] = _PALETTE

    try:
        if chart_type == "line" and x and y:
            sns.lineplot(data=df, x=x, y=y, hue=hue_val, ax=ax, **kwargs)
        elif chart_type == "bar" and x and y:
            sns.barplot(data=df, x=x, y=y, hue=hue_val, ax=ax,
                        estimator=np.mean, **kwargs)
        elif chart_type == "scatter" and x and y:
            sns.scatterplot(data=df, x=x, y=y, hue=hue_val,
                            ax=ax, alpha=0.75, **kwargs)
        elif chart_type == "hist" and (x or y):
            target = x or y
            sns.histplot(data=df, x=target, hue=hue_val,
                         kde=True, ax=ax, color=_ACCENT if not hue_val else None)
        elif chart_type == "box" and x and y:
            sns.boxplot(data=df, x=x, y=y, hue=hue_val, ax=ax, **kwargs)
        elif chart_type == "heatmap":
            num = df.select_dtypes(include=np.number)
            num = num.loc[:, ~num.columns.str.startswith("_outlier_")]
            if num.shape[1] < 2:
                plt.close(fig)
                return None
            corr = num.corr(numeric_only=True)
            sns.heatmap(corr, annot=True, fmt=".2f", cmap="crest", ax=ax,
                        linewidths=0.5, linecolor=_GRID)
        else:
            plt.close(fig)
            return None
    except Exception:
        plt.close(fig)
        return None

    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    plt.xticks(rotation=25, ha="right", fontsize=8)

    legend = ax.get_legend()
    if legend:
        legend.get_frame().set_facecolor(_CARD_BG)
        legend.get_frame().set_edgecolor(_GRID)
        for text in legend.get_texts():
            text.set_color(_TEXT)

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=_DARK_BG)
    plt.close(fig)
    buf.seek(0)
    return buf.read()

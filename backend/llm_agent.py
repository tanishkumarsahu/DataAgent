"""llm_agent.py — LLM chat agent and chart spec inference.

Uses the OpenAI Python SDK (compatible with any OpenAI-spec provider).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from openai import OpenAI


# ---------------------------------------------------------------------------
# Dataset context builder
# ---------------------------------------------------------------------------

def _build_context(df: pd.DataFrame) -> str:
    """Produce a compact textual profile to inject into the LLM prompt."""
    lines: list[str] = [
        f"Rows: {len(df)}, Columns: {len(df.columns)}",
        f"Column names & dtypes: {', '.join(f'{c}({t})' for c, t in df.dtypes.items())}",
    ]

    numeric = df.select_dtypes(include=np.number)
    if not numeric.empty:
        lines.append("Numeric summary:")
        lines.append(numeric.describe().round(3).to_string())

    cat_cols = df.select_dtypes(include="object").columns
    if len(cat_cols):
        lines.append("Categorical top values:")
        for col in cat_cols[:6]:  # limit to avoid huge prompts
            top = df[col].value_counts().head(5).to_dict()
            lines.append(f"  {col}: {top}")

    lines.append("Sample rows (first 8):")
    lines.append(df.head(8).to_string(index=False))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Chat agent
# ---------------------------------------------------------------------------

@dataclass
class DataChatAgent:
    """Wraps an OpenAI client to answer questions about a DataFrame."""

    client: OpenAI
    model_name: str
    dataframe: pd.DataFrame
    history: list[dict[str, str]] = field(default_factory=list)

    _SYSTEM_PROMPT = (
        "You are DataAgent, an expert data analyst AI. "
        "You have been given a dataset and must answer the user's questions accurately. "
        "Always reference specific column names, numbers, and statistics from the dataset. "
        "Be concise but thorough. Format numbers clearly. "
        "If asked about trends, correlations, or patterns, explain them with supporting data."
    )

    def ask(self, question: str) -> str:
        """Send a user question, maintain conversation history, return answer text."""

        context = _build_context(self.dataframe)
        if not self.history:
            # Inject dataset context in the first user turn
            first_content = (
                f"Here is the dataset I want to discuss:\n\n{context}\n\n"
                f"My first question: {question.strip()}"
            )
            self.history.append({"role": "user", "content": first_content})
        else:
            self.history.append({"role": "user", "content": question.strip()})

        messages = [{"role": "system", "content": self._SYSTEM_PROMPT}] + self.history

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.2,
        )
        answer = (response.choices[0].message.content or "").strip()
        self.history.append({"role": "assistant", "content": answer})
        return answer


# ---------------------------------------------------------------------------
# Agent factory (one agent per session stored server-side in memory)
# ---------------------------------------------------------------------------

_agents: dict[str, DataChatAgent] = {}


def get_or_create_agent(
    session_id: str,
    api_key: str,
    model_name: str,
    df: pd.DataFrame,
) -> DataChatAgent:
    """Return an existing agent for this session or create a new one."""
    if session_id not in _agents or _agents[session_id].dataframe is not df:
        client = OpenAI(api_key=api_key)
        _agents[session_id] = DataChatAgent(
            client=client, model_name=model_name, dataframe=df
        )
    return _agents[session_id]


def reset_agent(session_id: str) -> None:
    """Clear the agent for a session (e.g. on new file upload)."""
    _agents.pop(session_id, None)


# ---------------------------------------------------------------------------
# Chart spec inference
# ---------------------------------------------------------------------------

_CHART_SCHEMA = (
    '{"make_chart": bool, '
    '"chart_type": "line|bar|scatter|hist|box|heatmap", '
    '"x": "<column_name_or_empty>", '
    '"y": "<column_name_or_empty>", '
    '"hue": "<column_name_or_empty>", '
    '"title": "<short title>"}'
)


def infer_chart_spec(
    question: str,
    df: pd.DataFrame,
    api_key: str,
    model_name: str,
) -> dict[str, Any] | None:
    """Ask the LLM to derive a chart specification from a natural-language question."""

    schema = ", ".join(f"{c}:{t}" for c, t in df.dtypes.items())
    prompt = (
        "You are a chart planner for a data analysis app. "
        "Given a question and a dataset schema, return ONLY a JSON object with this exact shape:\n"
        f"{_CHART_SCHEMA}\n\n"
        "Rules:\n"
        "- Set make_chart=false if no visualisation is appropriate.\n"
        "- x and y must be column names that exist in the schema (or empty string).\n"
        "- hue should be a categorical column or empty string.\n"
        "- For correlation questions, use heatmap.\n"
        "- For distributions, use hist.\n\n"
        f"Dataset schema: {schema}\n"
        f"Question: {question}"
    )

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    raw = (response.choices[0].message.content or "").strip()

    try:
        spec = _extract_json(raw)
    except Exception:
        return None

    if not isinstance(spec, dict) or not spec.get("make_chart"):
        return None
    return spec


def _extract_json(text: str) -> Any:
    """Strip markdown code fences then parse JSON."""
    cleaned = re.sub(r"^```[a-z]*\n?", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"```$", "", cleaned.strip())
    return json.loads(cleaned.strip())

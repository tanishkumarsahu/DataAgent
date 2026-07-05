"""main.py — FastAPI application entry point for DataAgent.

Routes:
  POST /api/upload    — parse uploaded file, return profile
  POST /api/clean     — run auto-cleaning pipeline, return report
  POST /api/chat      — LLM Q&A about the dataset
  POST /api/chart     — generate chart PNG from a question
  GET  /api/download  — download cleaned CSV
  GET  /               — health check
"""

from __future__ import annotations

import base64
import os
import uuid
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from chart_builder import build_chart_from_params, build_chart_png, validate_chart_spec
from data_handler import auto_clean, dataframe_to_excel_bytes, load_file, profile_dataframe
from llm_agent import get_or_create_agent, infer_chart_spec, reset_agent

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="DataAgent API", version="1.0.0")

# Configure CORS origins
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins = [o.strip() for o in frontend_url.split(",") if o.strip()]
    origins.extend(["http://localhost:5173", "http://127.0.0.1:5173"])
else:
    origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

# Ensure unique origins
origins = list(dict.fromkeys(origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store: session_id → DataFrame (raw and cleaned)
_raw_frames:     dict[str, pd.DataFrame] = {}
_cleaned_frames: dict[str, pd.DataFrame] = {}


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/")
def health():
    return {"status": "ok", "service": "DataAgent API"}


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)) -> dict[str, Any]:
    """Accept a CSV or XLSX file and return its profile + a session_id."""

    allowed = {".csv", ".xlsx", ".xls"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Use .csv or .xlsx.")

    file_bytes = await file.read()
    try:
        df = load_file(file_bytes, file.filename or "upload.csv")
    except Exception as exc:
        raise HTTPException(422, f"Could not parse file: {exc}") from exc

    session_id = str(uuid.uuid4())
    _raw_frames[session_id]     = df
    _cleaned_frames[session_id] = df.copy()   # will be overwritten on /clean
    reset_agent(session_id)

    profile = profile_dataframe(df)
    return {"session_id": session_id, "profile": profile, "filename": file.filename}


# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------

@app.post("/api/clean")
def clean_data(session_id: str = Form(...)) -> dict[str, Any]:
    """Run the automated cleaning pipeline on the uploaded dataset."""

    df = _get_frame(session_id, raw=True)
    cleaned_df, report = auto_clean(df)
    _cleaned_frames[session_id] = cleaned_df

    cleaned_profile = profile_dataframe(cleaned_df)
    return {"report": report, "cleaned_profile": cleaned_profile}


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    session_id: str
    question: str
    model_name: str = "gemini-2.0-flash"
    use_cleaned: bool = True


@app.post("/api/chat")
def chat(req: ChatRequest) -> dict[str, Any]:
    """Send a user question to the LLM agent and return the answer."""

    df = _get_frame(req.session_id, raw=not req.use_cleaned)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(500, "GEMINI_API_KEY is not configured on the backend server.")

    try:
        agent = get_or_create_agent(req.session_id, api_key, req.model_name, df)
        answer = agent.ask(req.question)
    except Exception as exc:
        raise HTTPException(500, f"LLM error: {exc}") from exc

    return {"answer": answer}


# ---------------------------------------------------------------------------
# Chart
# ---------------------------------------------------------------------------

class ChartRequest(BaseModel):
    session_id: str
    question: str
    model_name: str = "gemini-2.0-flash"
    use_cleaned: bool = True


@app.post("/api/chart")
def generate_chart(req: ChartRequest) -> dict[str, Any]:
    """Infer a chart spec from the user question and return a base64-encoded PNG."""

    df = _get_frame(req.session_id, raw=not req.use_cleaned)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(500, "GEMINI_API_KEY is not configured on the backend server.")

    spec = infer_chart_spec(req.question, df, api_key, req.model_name)
    if not spec:
        return {"chart": None, "message": "No chart applicable for this question."}

    png_bytes = build_chart_png(spec, df)
    if not png_bytes:
        return {"chart": None, "message": "Chart could not be rendered."}

    encoded = base64.b64encode(png_bytes).decode("utf-8")
    return {"chart": encoded, "spec": spec}


# ---------------------------------------------------------------------------
# Manual Chart — user picks columns & chart type (no AI involved)
# ---------------------------------------------------------------------------

class ManualChartRequest(BaseModel):
    session_id: str
    chart_type: str
    x_column: str = ""
    y_column: str = ""
    hue_column: str = ""
    title: str = ""
    use_cleaned: bool = True


@app.post("/api/manual-chart")
def manual_chart(req: ManualChartRequest) -> dict[str, Any]:
    """Generate a chart from user-selected columns and chart type."""

    df = _get_frame(req.session_id, raw=not req.use_cleaned)

    error = validate_chart_spec(df, req.chart_type, req.x_column, req.y_column)
    if error:
        return {"chart": None, "error": error}

    png_bytes = build_chart_from_params(
        df,
        chart_type=req.chart_type,
        x_column=req.x_column,
        y_column=req.y_column,
        hue_column=req.hue_column,
        title=req.title,
    )
    if not png_bytes:
        return {"chart": None, "error": "Chart could not be rendered. Check your column selections."}

    encoded = base64.b64encode(png_bytes).decode("utf-8")
    return {"chart": encoded, "error": None}


# ---------------------------------------------------------------------------
# Download cleaned CSV
# ---------------------------------------------------------------------------

@app.get("/api/download")
def download_excel(session_id: str) -> StreamingResponse:
    """Return the cleaned DataFrame as a downloadable Excel file."""

    df = _get_frame(session_id, raw=False)
    excel_bytes = dataframe_to_excel_bytes(df)

    import io
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=cleaned_data.xlsx"},
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_frame(session_id: str, *, raw: bool) -> pd.DataFrame:
    store = _raw_frames if raw else _cleaned_frames
    df = store.get(session_id)
    if df is None:
        raise HTTPException(404, "Session not found. Please upload a file first.")
    return df


# ---------------------------------------------------------------------------
# Dev entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


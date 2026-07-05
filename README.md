# DataAgent 🧹

> AI-powered automated data cleaning and LLM-driven dataset analysis.

Upload a `.csv` or `.xlsx` file, let the automated pipeline clean it, then chat with an LLM that knows your data inside-out.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite (plain CSS, no Tailwind) |
| Backend | Python 3.11+ · FastAPI · uvicorn |
| Data | pandas · numpy · openpyxl |
| Charts | matplotlib · seaborn |
| LLM | Gemini API (gemini-2.0-flash or compatible model) |

---

## Project Structure

```
DataAgent/
├── backend/
│   ├── main.py           ← FastAPI routes
│   ├── data_handler.py   ← File parsing + cleaning pipeline
│   ├── llm_agent.py      ← LLM chat agent + chart spec inference
│   ├── chart_builder.py  ← matplotlib/seaborn → PNG bytes
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── index.css      ← Design system (dark theme)
│       ├── api/client.js  ← All API calls
│       └── components/
│           ├── Sidebar.jsx
│           ├── UploadPanel.jsx
│           ├── DataOverview.jsx
│           ├── CleaningReport.jsx
│           └── ChatPanel.jsx
└── README.md
```

---

## Quick Start

### 1 — Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
# → API running at http://localhost:8000
```

### 2 — Frontend

```bash
cd frontend
npm install
npm run dev
# → App running at http://localhost:5173
```

### 3 — Use It

1. Configure your environment:
   - In `backend/`, copy `.env.example` to `.env` and fill in your `GEMINI_API_KEY`.
   - In `frontend/`, copy `.env.example` to `.env` (the defaults work for local dev).
2. Open `http://localhost:5173`
3. Drag & drop a `.csv` or `.xlsx` file
4. Review the dataset overview
5. Click **Run Cleaner** to auto-clean
6. Download the cleaned CSV
7. Chat with your data using natural language (powered by Gemini)

---

## Cleaning Pipeline

The automated cleaner performs these steps in order:

| Step | Action |
|------|--------|
| 1 | Remove fully-duplicate rows |
| 2 | Strip leading/trailing whitespace from string columns |
| 3 | Fill numeric NaN values with column **median** |
| 4 | Fill categorical NaN values with column **mode** |
| 5 | Flag outliers via 1.5×IQR rule (adds `_outlier_*` columns) |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/api/upload` | Upload CSV/XLSX → returns profile + session_id |
| `POST` | `/api/clean` | Run cleaning pipeline |
| `POST` | `/api/chat` | LLM Q&A about dataset |
| `POST` | `/api/chart` | Infer & render chart as base64 PNG |
| `GET` | `/api/download` | Download cleaned CSV |

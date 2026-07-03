import { useState } from "react";
import { generateManualChart } from "../api/client";

const CHART_TYPES = [
  { value: "line",     label: "Line",     icon: "📈", desc: "Trend over a continuous axis" },
  { value: "bar",      label: "Bar",      icon: "📊", desc: "Compare values across categories" },
  { value: "scatter",  label: "Scatter",  icon: "✨", desc: "Relationship between two numeric columns" },
  { value: "hist",     label: "Histogram",icon: "🌊", desc: "Distribution of a numeric column" },
  { value: "box",      label: "Box",      icon: "📦", desc: "Spread & outliers of numeric data" },
  { value: "heatmap",  label: "Heatmap",  icon: "🔥", desc: "Correlation matrix of numeric columns" },
];

export default function GraphPanel({ sessionId, profile, useCleaned }) {
  const [chartType, setChartType] = useState("bar");
  const [xColumn,   setXColumn]   = useState("");
  const [yColumn,   setYColumn]   = useState("");
  const [hueColumn, setHueColumn] = useState("");
  const [title,     setTitle]     = useState("");
  const [chart,     setChart]     = useState(null);
  const [error,     setError]     = useState(null);
  const [loading,   setLoading]   = useState(false);

  const hasData = !!sessionId && !!profile;
  const columns = profile?.columns || [];

  const needsBothAxis = ["line", "bar", "scatter", "box"].includes(chartType);
  const needsXOnly = chartType === "hist";
  const needsNone = chartType === "heatmap";

  async function handleGenerate() {
    setChart(null);
    setError(null);

    if (!sessionId) {
      setError("Please upload a dataset first before generating a graph.");
      return;
    }

    setLoading(true);
    try {
      const res = await generateManualChart({
        sessionId,
        chartType,
        xColumn,
        yColumn,
        hueColumn,
        title,
        useCleaned,
      });

      if (res.error) {
        setError(res.error);
      } else if (res.chart) {
        setChart(res.chart);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card fade-up">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="step-badge step-active">5</div>
          <div>
            <h2>Build a Graph</h2>
            <p style={{ fontSize: ".8rem", color: "var(--text-secondary)", marginTop: ".1rem" }}>
              Pick columns and chart type — no AI needed
            </p>
          </div>
        </div>
        {hasData && (
          <span className="badge badge-cyan" style={{ fontSize: ".68rem" }}>
            {profile.cols} columns available
          </span>
        )}
      </div>

      {!hasData ? (
        <div style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "2.5rem 1rem",
          gap: "1rem",
          textAlign: "center",
        }}>
          <div style={{
            width: 64, height: 64,
            borderRadius: "50%",
            background: "rgba(124,58,237,.12)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "1.75rem",
          }}>
            📊
          </div>
          <div>
            <h3 style={{ marginBottom: ".3rem" }}>No dataset loaded</h3>
            <p style={{ color: "var(--text-muted)", fontSize: ".85rem", maxWidth: 360 }}>
              Upload a CSV or Excel file above, then come here to create custom graphs from your columns.
            </p>
          </div>
        </div>
      ) : (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
            <div>
              <label style={{ fontSize: ".75rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em", display: "block", marginBottom: ".35rem" }}>
                Chart Type
              </label>
              <select
                className="input"
                value={chartType}
                onChange={e => { setChartType(e.target.value); setChart(null); setError(null); }}
                style={{ cursor: "pointer" }}
              >
                {CHART_TYPES.map(t => (
                  <option key={t.value} value={t.value}>{t.icon} {t.label} — {t.desc}</option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ fontSize: ".75rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em", display: "block", marginBottom: ".35rem" }}>
                Title (optional)
              </label>
              <input
                className="input"
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="My Chart"
              />
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: needsNone ? "1fr" : "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
            {!needsNone && (
              <div>
                <label style={{ fontSize: ".75rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em", display: "block", marginBottom: ".35rem" }}>
                  X-axis {needsXOnly ? "(numeric column)" : "Column"}
                </label>
                <select
                  className="input"
                  value={xColumn}
                  onChange={e => setXColumn(e.target.value)}
                  style={{ cursor: "pointer" }}
                >
                  <option value="">— Select —</option>
                  {columns.map(c => (
                    <option key={c.name} value={c.name}>{c.name} ({c.dtype})</option>
                  ))}
                </select>
              </div>
            )}

            {needsBothAxis && (
              <div>
                <label style={{ fontSize: ".75rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em", display: "block", marginBottom: ".35rem" }}>
                  Y-axis Column (numeric)
                </label>
                <select
                  className="input"
                  value={yColumn}
                  onChange={e => setYColumn(e.target.value)}
                  style={{ cursor: "pointer" }}
                >
                  <option value="">— Select —</option>
                  {columns.filter(c => c.dtype === "float64" || c.dtype === "int64").map(c => (
                    <option key={c.name} value={c.name}>{c.name} ({c.dtype})</option>
                  ))}
                </select>
              </div>
            )}

            {!needsNone && (
              <div>
                <label style={{ fontSize: ".75rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em", display: "block", marginBottom: ".35rem" }}>
                  Group by (optional)
                </label>
                <select
                  className="input"
                  value={hueColumn}
                  onChange={e => setHueColumn(e.target.value)}
                  style={{ cursor: "pointer" }}
                >
                  <option value="">— None —</option>
                  {columns.filter(c => c.dtype === "object" || c.dtype === "category").map(c => (
                    <option key={c.name} value={c.name}>{c.name}</option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <button
            className="btn btn-primary btn-lg w-full"
            onClick={handleGenerate}
            disabled={loading || !sessionId}
            style={{ marginBottom: "1rem", justifyContent: "center" }}
          >
            {loading ? <><span className="spinner" style={{ width: 16, height: 16 }} /> Generating…</> : "🚀 Generate Graph"}
          </button>
        </>
      )}

      {error && (
        <div style={{
          background: "rgba(239,68,68,.12)",
          border: "1px solid var(--danger)",
          borderRadius: "var(--radius-sm)",
          padding: ".75rem 1rem",
          color: "#fca5a5",
          fontSize: ".85rem",
          marginBottom: "1rem",
        }}>
          <strong>Cannot create graph:</strong> {error}
        </div>
      )}

      {chart && (
        <div style={{
          borderRadius: "var(--radius-sm)",
          border: "1px solid var(--border)",
          overflow: "hidden",
          background: "var(--bg-card2)",
        }}>
          <img
            src={`data:image/png;base64,${chart}`}
            alt="Generated chart"
            style={{
              width: "100%",
              display: "block",
            }}
          />
        </div>
      )}
    </div>
  );
}

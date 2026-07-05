import { downloadCleanedExcel } from "../api/client";

const ACTION_ICONS = {
  remove_duplicates:    { icon: "🔁", color: "var(--danger)" },
  strip_whitespace:     { icon: "✂️", color: "var(--accent-2)" },
  fill_numeric_nulls:   { icon: "🔢", color: "var(--accent)" },
  fill_categorical_nulls: { icon: "🏷️", color: "var(--accent)" },
  flag_outliers:        { icon: "⚡", color: "var(--warn)" },
  no_issues:            { icon: "✅", color: "var(--success)" },
};

export default function CleaningReport({ report, cleanedProfile, sessionId, loading, onClean }) {
  return (
    <div className="card fade-up">
      {/* Header */}
      <div className="flex-header-responsive mb-4">
        <div className="flex items-center gap-3">
          <div className={`step-badge ${report ? "step-done" : "step-active"}`}>
            {report ? "✓" : "2"}
          </div>
          <div>
            <h2>Auto Cleaning</h2>
            <p style={{ fontSize: ".8rem", color: "var(--text-secondary)", marginTop: ".15rem" }}>
              AI-powered cleaning pipeline
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            id="run-clean-btn"
            className="btn btn-primary btn-sm"
            onClick={onClean}
            disabled={loading}
          >
            {loading ? <><span className="spinner" style={{ width: 14, height: 14 }} />Cleaning…</> : "▶ Run Cleaner"}
          </button>

          {report && sessionId && (
            <button
              id="download-excel-btn"
              className="btn btn-secondary btn-sm"
              onClick={() => downloadCleanedExcel(sessionId)}
            >
              ⬇ Download Excel
            </button>
          )}
        </div>
      </div>

      {/* Result */}
      {report ? (
        <>
          {/* Row delta */}
          {report.rows_before !== report.rows_after && (
            <div style={{
              background: "rgba(239,68,68,.07)",
              border: "1px solid rgba(239,68,68,.2)",
              borderRadius: "var(--radius-sm)",
              padding: ".6rem 1rem",
              fontSize: ".82rem",
              color: "var(--danger)",
              marginBottom: "1rem",
            }}>
              Row count: {report.rows_before} → {report.rows_after}
              {" "}({report.rows_before - report.rows_after} removed)
            </div>
          )}

          {/* Steps */}
          <div style={{ display: "flex", flexDirection: "column", gap: ".6rem" }}>
            {report.steps.map((step, i) => {
              const meta = ACTION_ICONS[step.action] || { icon: "🔧", color: "var(--text-secondary)" };
              return (
                <div
                  key={i}
                  className="flex gap-3"
                  style={{
                    padding: ".75rem 1rem",
                    background: "var(--bg-card2)",
                    borderRadius: "var(--radius-sm)",
                    border: "1px solid var(--border)",
                    alignItems: "flex-start",
                  }}
                >
                  <span style={{ fontSize: "1.1rem", flexShrink: 0, marginTop: 1 }}>{meta.icon}</span>
                  <div>
                    <span
                      className="badge"
                      style={{
                        background: `${meta.color}18`,
                        color: meta.color,
                        border: `1px solid ${meta.color}44`,
                        marginBottom: ".3rem",
                        textTransform: "none",
                        fontSize: ".7rem",
                      }}
                    >
                      {step.action.replace(/_/g, " ")}
                    </span>
                    <p style={{ fontSize: ".82rem", color: "var(--text-primary)", lineHeight: 1.5 }}>
                      {step.detail}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Cleaned stats */}
          {cleanedProfile && (
            <div style={{
              marginTop: "1rem",
              padding: ".75rem 1rem",
              background: "rgba(16,185,129,.07)",
              border: "1px solid rgba(16,185,129,.2)",
              borderRadius: "var(--radius-sm)",
              fontSize: ".82rem",
              color: "var(--success)",
            }}>
              ✅ Cleaned dataset: {cleanedProfile.rows.toLocaleString()} rows ×{" "}
              {cleanedProfile.cols} columns — {cleanedProfile.missing_total} missing values remaining
            </div>
          )}
        </>
      ) : (
        <p style={{ color: "var(--text-muted)", fontSize: ".85rem" }}>
          Click <strong style={{ color: "var(--text-primary)" }}>Run Cleaner</strong> to automatically fix duplicates,
          missing values, whitespace issues, and flag outliers.
        </p>
      )}
    </div>
  );
}

export default function DataOverview({ profile, filename }) {
  if (!profile) return null;
  const { rows, cols, missing_total, memory_kb, columns, preview } = profile;

  function dtypeBadge(dtype) {
    if (dtype.includes("int") || dtype.includes("float")) return "badge badge-cyan";
    if (dtype.includes("object") || dtype.includes("str"))  return "badge badge-purple";
    if (dtype.includes("date") || dtype.includes("time"))   return "badge badge-amber";
    if (dtype.includes("bool"))                             return "badge badge-green";
    return "badge badge-red";
  }

  return (
    <div className="fade-up">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="step-badge step-done">✓</div>
        <div>
          <h2>Dataset Overview</h2>
          <p style={{ fontSize: ".8rem", color: "var(--text-secondary)", marginTop: ".15rem" }}>
            <span style={{ color: "var(--accent)" }}>📄</span> {filename}
          </p>
        </div>
      </div>

      {/* Stat cards */}
      <div className="stat-grid mb-4">
        <StatCard label="Rows"          value={rows.toLocaleString()}             icon="🔢" color="var(--accent)" />
        <StatCard label="Columns"       value={cols.toLocaleString()}             icon="📋" color="var(--accent-2)" />
        <StatCard label="Missing Cells" value={missing_total.toLocaleString()}    icon="❓" color={missing_total ? "var(--warn)" : "var(--success)"} />
        <StatCard label="Memory"        value={`${memory_kb} KB`}                 icon="💾" color="var(--success)" />
      </div>

      {/* Column info */}
      <div className="card mb-4">
        <h3 className="mb-2" style={{ color: "var(--text-secondary)", fontSize: ".78rem", textTransform: "uppercase", letterSpacing: ".07em" }}>
          Column Details
        </h3>
        <div style={{ display: "flex", flexWrap: "wrap", gap: ".5rem" }}>
          {columns.map(col => (
            <div
              key={col.name}
              style={{
                background: "var(--bg-card2)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius-sm)",
                padding: ".4rem .75rem",
                fontSize: ".78rem",
              }}
            >
              <span style={{ fontWeight: 600, color: "var(--text-primary)", marginRight: ".4rem" }}>{col.name}</span>
              <span className={dtypeBadge(col.dtype)}>{col.dtype}</span>
              {col.null_count > 0 && (
                <span style={{ marginLeft: ".4rem", color: "var(--warn)", fontSize: ".7rem" }}>
                  {col.null_pct}% null
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Preview table */}
      <div className="card">
        <h3 style={{ marginBottom: ".75rem", color: "var(--text-secondary)", fontSize: ".78rem", textTransform: "uppercase", letterSpacing: ".07em" }}>
          Data Preview <span style={{ color: "var(--text-muted)", fontWeight: 400 }}>(first 30 rows)</span>
        </h3>
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ color: "var(--text-muted)" }}>#</th>
                {Object.keys(preview[0] || {}).map(k => <th key={k}>{k}</th>)}
              </tr>
            </thead>
            <tbody>
              {preview.map((row, i) => (
                <tr key={i}>
                  <td style={{ color: "var(--text-muted)", fontSize: ".72rem" }}>{i + 1}</td>
                  {Object.values(row).map((val, j) => (
                    <td key={j} style={{ color: val === null ? "var(--text-muted)" : "var(--text-primary)" }}>
                      {val === null ? <span style={{ fontStyle: "italic", opacity: .5 }}>null</span> : String(val)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, icon, color }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ color }}>{value}</div>
      <div style={{ position: "absolute", top: "1rem", right: "1rem", fontSize: "1.4rem", opacity: .4 }}>{icon}</div>
    </div>
  );
}

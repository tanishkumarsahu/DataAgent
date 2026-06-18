import { useState } from "react";

export default function Sidebar({ apiKey, setApiKey, modelName, setModelName, autoChart, setAutoChart, useCleaned, setUseCleaned }) {
  const [showKey, setShowKey] = useState(false);

  return (
    <aside style={{
      width: 260,
      flexShrink: 0,
      background: "var(--bg-card)",
      borderRight: "1px solid var(--border)",
      padding: "1.5rem 1.25rem",
      display: "flex",
      flexDirection: "column",
      gap: "1.5rem",
      height: "100vh",
      position: "sticky",
      top: 0,
      overflowY: "auto",
    }}>
      {/* Brand */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <div style={{
            width: 34, height: 34,
            borderRadius: 8,
            background: "var(--accent-grad)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "1rem",
          }}>🧹</div>
          <h2 style={{ fontSize: "1.1rem" }}>DataAgent</h2>
        </div>
        <p style={{ fontSize: ".72rem", color: "var(--text-muted)", lineHeight: 1.5 }}>
          AI-powered data cleaning &amp; insights
        </p>
      </div>

      <div className="divider" style={{ margin: 0 }} />

      {/* API Key */}
      <div>
        <label style={{ fontSize: ".75rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em", display: "block", marginBottom: ".5rem" }}>
          OpenAI API Key
        </label>
        <div style={{ position: "relative" }}>
          <input
            id="api-key-input"
            className="input"
            type={showKey ? "text" : "password"}
            value={apiKey}
            onChange={e => setApiKey(e.target.value)}
            placeholder="sk-..."
            style={{ paddingRight: "2.5rem" }}
          />
          <button
            onClick={() => setShowKey(v => !v)}
            style={{
              position: "absolute", right: ".6rem", top: "50%",
              transform: "translateY(-50%)",
              background: "none", border: "none",
              cursor: "pointer", color: "var(--text-muted)", fontSize: ".85rem",
            }}
            title={showKey ? "Hide" : "Show"}
          >
            {showKey ? "🙈" : "👁️"}
          </button>
        </div>
        {!apiKey && (
          <p style={{ fontSize: ".7rem", color: "var(--warn)", marginTop: ".35rem" }}>
            ⚠ Required for chat &amp; charts
          </p>
        )}
      </div>

      {/* Model */}
      <div>
        <label style={{ fontSize: ".75rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em", display: "block", marginBottom: ".5rem" }}>
          Model
        </label>
        <input
          id="model-name-input"
          className="input"
          type="text"
          value={modelName}
          onChange={e => setModelName(e.target.value)}
          placeholder="gpt-4o"
        />
      </div>

      {/* Toggles */}
      <div style={{ display: "flex", flexDirection: "column", gap: ".85rem" }}>
        <label style={{ fontSize: ".75rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".06em" }}>
          Options
        </label>
        <Toggle id="auto-chart-toggle" label="Auto-generate chart" checked={autoChart} onChange={setAutoChart} />
        <Toggle id="use-cleaned-toggle" label="Use cleaned data for chat" checked={useCleaned} onChange={setUseCleaned} />
      </div>

      <div style={{ flex: 1 }} />

      {/* Footer */}
      <p style={{ fontSize: ".68rem", color: "var(--text-muted)", lineHeight: 1.6 }}>
        Upload a <strong style={{ color: "var(--text-secondary)" }}>.csv</strong> or{" "}
        <strong style={{ color: "var(--text-secondary)" }}>.xlsx</strong> file, then clean,
        explore, and chat with your data.
      </p>
    </aside>
  );
}

function Toggle({ id, label, checked, onChange }) {
  return (
    <label htmlFor={id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", cursor: "pointer", gap: ".75rem" }}>
      <span style={{ fontSize: ".82rem", color: "var(--text-primary)" }}>{label}</span>
      <div
        id={id}
        onClick={() => onChange(v => !v)}
        role="switch"
        aria-checked={checked}
        style={{
          width: 38, height: 22,
          borderRadius: 99,
          background: checked ? "var(--accent)" : "var(--border)",
          position: "relative",
          transition: "background .2s",
          flexShrink: 0,
        }}
      >
        <div style={{
          position: "absolute",
          top: 3, left: checked ? 18 : 3,
          width: 16, height: 16,
          borderRadius: "50%",
          background: "#fff",
          transition: "left .2s",
          boxShadow: "0 1px 4px rgba(0,0,0,.3)",
        }} />
      </div>
    </label>
  );
}

import { useCallback, useState } from "react";

export default function UploadPanel({ onUpload, loading }) {
  const [dragging, setDragging] = useState(false);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState("");

  const ALLOWED = ["text/csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                   "application/vnd.ms-excel"];

  function validate(file) {
    if (!file) return "No file selected.";
    const ext = file.name.split(".").pop().toLowerCase();
    if (!["csv","xlsx","xls"].includes(ext)) return "Only .csv and .xlsx files are supported.";
    return "";
  }

  function pick(file) {
    const err = validate(file);
    setError(err);
    if (!err) setSelected(file);
  }

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    pick(e.dataTransfer.files[0]);
  }, []);

  function handleSubmit() {
    if (!selected || error) return;
    onUpload(selected);
  }

  return (
    <div className="card fade-up" style={{ maxWidth: 640, margin: "0 auto" }}>
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="step-badge step-active">1</div>
        <div>
          <h2>Upload Dataset</h2>
          <p style={{ fontSize: ".8rem", color: "var(--text-secondary)", marginTop: ".15rem" }}>
            Drop a <strong>.csv</strong> or <strong>.xlsx</strong> file to get started
          </p>
        </div>
      </div>

      {/* Drop zone */}
      <div
        id="dropzone"
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => document.getElementById("file-input").click()}
        style={{
          border: `2px dashed ${dragging ? "var(--accent)" : selected ? "var(--success)" : "var(--border)"}`,
          borderRadius: "var(--radius-md)",
          padding: "2.5rem 1.5rem",
          textAlign: "center",
          cursor: "pointer",
          background: dragging ? "rgba(124,58,237,.07)" : selected ? "rgba(16,185,129,.05)" : "var(--bg-input)",
          transition: "all var(--transition)",
          position: "relative",
        }}
      >
        <input
          id="file-input"
          type="file"
          accept=".csv,.xlsx,.xls"
          style={{ display: "none" }}
          onChange={e => pick(e.target.files[0])}
        />

        <div style={{ fontSize: "2.5rem", marginBottom: ".75rem" }}>
          {selected ? "📊" : "📁"}
        </div>

        {selected ? (
          <>
            <p style={{ fontWeight: 700, color: "var(--success)", fontSize: ".95rem" }}>
              {selected.name}
            </p>
            <p style={{ fontSize: ".75rem", color: "var(--text-muted)", marginTop: ".25rem" }}>
              {(selected.size / 1024).toFixed(1)} KB • Click to change
            </p>
          </>
        ) : (
          <>
            <p style={{ fontWeight: 600, color: "var(--text-primary)" }}>
              Drag &amp; drop your file here
            </p>
            <p style={{ fontSize: ".8rem", color: "var(--text-muted)", marginTop: ".25rem" }}>
              or click to browse
            </p>
          </>
        )}
      </div>

      {error && (
        <p style={{ color: "var(--danger)", fontSize: ".8rem", marginTop: ".5rem" }}>⚠ {error}</p>
      )}

      <button
        id="upload-btn"
        className="btn btn-primary btn-lg w-full mt-4"
        disabled={!selected || !!error || loading}
        onClick={handleSubmit}
        style={{ justifyContent: "center" }}
      >
        {loading ? <><span className="spinner" />Uploading…</> : "✦ Analyze Dataset"}
      </button>
    </div>
  );
}

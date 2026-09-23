import { useState } from "react";
import { regenerateSummary, listSummaries } from "../api";

const STATUS_LABEL = {
  FULLY_UTILIZED: "Fully Utilized",
  UNDER_UTILIZED: "Under-Utilized",
  OVER_UTILIZED: "Over-Utilized",
};

export default function ResultPage({ comparison, onStartOver }) {
  const [summary, setSummary] = useState(comparison.summary);
  const [result] = useState(comparison.result);
  const extraction = comparison.extraction || {};
  const [history, setHistory] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleRegenerate() {
    setBusy(true);
    setError("");
    try {
      const next = await regenerateSummary(comparison.comparison_id);
      setSummary(next);
      setHistory(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function toggleHistory() {
    if (history) {
      setHistory(null);
      return;
    }
    const versions = await listSummaries(comparison.comparison_id);
    setHistory(versions);
  }

  const statusClass = `pill-${result.overall_status.toLowerCase()}`;

  return (
    <div className="card">
      <div className="result-header">
        <h2>Comparison Result</h2>
        <span className={`pill ${statusClass}`}>
          {STATUS_LABEL[result.overall_status] || result.overall_status}
        </span>
      </div>

      {extraction.mismatch_note && (
        <div className="warning-banner">
          <strong>These documents may not be a matching pair.</strong>
          <span>{extraction.mismatch_note}</span>
        </div>
      )}

      {extraction.consistency_note && (
        <div className="notice-banner">
          <strong>Points to reconcile</strong>
          <span>{extraction.consistency_note}</span>
          <span className="notice-foot">
            Paperwork differences only &mdash; the documents still look like a pair.
          </span>
        </div>
      )}

      <div className="stat-grid">
        <div className="stat-tile">
          <span className="stat-label">Sanctioned</span>
          <span className="stat-value">Rs {result.sanction_total}</span>
          {extraction.sanctioned_snippet && (
            <span className="snippet">&quot;{extraction.sanctioned_snippet}&quot;</span>
          )}
        </div>
        <div className="stat-tile">
          <span className="stat-label">Expenditure</span>
          <span className="stat-value">Rs {result.expenditure_total}</span>
          {extraction.expenditure_snippet && (
            <span className="snippet">&quot;{extraction.expenditure_snippet}&quot;</span>
          )}
        </div>
        <div className="stat-tile">
          <span className="stat-label">Difference</span>
          <span className="stat-value">Rs {result.difference}</span>
        </div>
        <div className="stat-tile">
          <span className="stat-label">Utilization</span>
          <span className="stat-value">{result.utilization_percentage}%</span>
        </div>
      </div>

      <div className="stat-tile stat-tile-wide">
        <span className="stat-label">Expenditure type (sanctioned purpose)</span>
        <span className="stat-value stat-value-text">{result.expenditure_type || "—"}</span>
        {extraction.type_snippet && (
          <span className="snippet">&quot;{extraction.type_snippet}&quot;</span>
        )}
      </div>

      {extraction.uc_purpose_snippet && (
        <div className="caution-box">
          <span className="stat-label">Actual spending recorded against (per UC)</span>
          <p>{extraction.uc_purpose_snippet}</p>
          <span className="hint">
            Worth checking this matches the sanctioned purpose above — the UC breaks spending
            down by category and this is where the money actually moved.
          </span>
        </div>
      )}

      {extraction.remarks_snippet && (
        <div className="remarks-box">
          <span className="stat-label">Remark in the UC document</span>
          <p>{extraction.remarks_snippet}</p>
        </div>
      )}

      <h3>Summary (v{summary.version})</h3>
      <p className="summary-text">{summary.summary_text}</p>

      {error && <p className="error">{error}</p>}
      <div className="actions">
        <button onClick={handleRegenerate} disabled={busy}>
          {busy ? "Regenerating..." : "Regenerate Summary"}
        </button>
        <button className="secondary" onClick={toggleHistory}>
          {history ? "Hide previous versions" : "Show previous versions"}
        </button>
        <button className="secondary" onClick={onStartOver}>
          Start a new comparison
        </button>
      </div>

      {history && (
        <ul className="history">
          {history.map((row) => (
            <li key={row.version}>
              v{row.version}
              {row.is_current ? " (current)" : ""}: {row.summary_text}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

import { useState } from "react";
import { getComparison, deleteComparison } from "../api";

function formatDate(iso) {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

// One row/card in the history list. Collapsed: name, date, status pill.
// Expanded (click to toggle): links to the original PDFs, the current
// summary below them, and a delete action. Detail is fetched lazily, once,
// the first time a row is opened.
export default function HistoryRow({ row, onOpenResult, onDeleted }) {
  const [expanded, setExpanded] = useState(false);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function toggle() {
    const next = !expanded;
    setExpanded(next);
    if (next && !detail) {
      setLoading(true);
      setError("");
      try {
        setDetail(await getComparison(row.comparison_id));
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
  }

  async function handleDelete(event) {
    event.stopPropagation();
    if (!window.confirm("Delete this comparison? This removes it and its documents for good.")) {
      return;
    }
    setBusy(true);
    setError("");
    try {
      await deleteComparison(row.comparison_id);
      onDeleted(row.comparison_id);
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  const docs = detail?.documents || [];
  const sanction = docs.find((d) => d.document_type === "SANCTION");
  const uc = docs.find((d) => d.document_type === "UC");

  return (
    <li className={`history-row ${expanded ? "expanded" : ""}`}>
      <div className="history-row-header" onClick={toggle}>
        <div className="history-row-main">
          <span className="history-row-title">
            {row.sanction_file_name || "(sanction)"} vs {row.uc_file_name || "(UC)"}
          </span>
          <span className="history-row-date">{formatDate(row.created_at)}</span>
        </div>
        <div className="history-row-side">
          {row.overall_status ? (
            <span className={`pill pill-${row.overall_status.toLowerCase()}`}>
              {row.overall_status.replace("_", " ")} · {row.utilization_percentage}%
            </span>
          ) : (
            <span className="pill pill-pending">{row.status}</span>
          )}
          <span className={`chevron ${expanded ? "chevron-open" : ""}`}>›</span>
        </div>
      </div>

      {expanded && (
        <div className="history-row-body">
          {loading && <p className="hint">Loading…</p>}
          {error && <p className="error">{error}</p>}

          {detail && (
            <>
              <div className="doc-links">
                {sanction && (
                  <a href={sanction.view_url} target="_blank" rel="noreferrer">
                    View Sanction Letter
                  </a>
                )}
                {uc && (
                  <a href={uc.view_url} target="_blank" rel="noreferrer">
                    View UC Document
                  </a>
                )}
              </div>

              {detail.summary ? (
                <p className="summary-text summary-text-compact">{detail.summary.summary_text}</p>
              ) : (
                <p className="hint">No summary yet — this comparison was never confirmed.</p>
              )}

              <div className="history-row-actions">
                <button className="secondary" onClick={() => onOpenResult(detail)}>
                  Open full result
                </button>
                <button className="danger" onClick={handleDelete} disabled={busy}>
                  {busy ? "Deleting..." : "Delete"}
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </li>
  );
}

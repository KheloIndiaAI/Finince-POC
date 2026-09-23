import { useEffect, useState } from "react";
import { listComparisons } from "../api";
import HistoryRow from "../components/HistoryRow";

export default function HistoryPage({ onOpen }) {
  const [rows, setRows] = useState(null);
  const [q, setQ] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [error, setError] = useState("");
  const [viewMode, setViewMode] = useState("list"); // list | grid

  async function load(filters) {
    setError("");
    try {
      setRows(await listComparisons(filters));
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load({});
  }, []);

  function handleSearch(event) {
    event.preventDefault();
    load({ q, dateFrom, dateTo });
  }

  function handleDeleted(comparisonId) {
    setRows((prev) => prev.filter((r) => r.comparison_id !== comparisonId));
  }

  return (
    <div className="card">
      <div className="history-top">
        <h2>Past comparisons</h2>
        <div className="view-toggle">
          <button
            className={viewMode === "list" ? "" : "secondary"}
            onClick={() => setViewMode("list")}
            type="button"
          >
            List
          </button>
          <button
            className={viewMode === "grid" ? "" : "secondary"}
            onClick={() => setViewMode("grid")}
            type="button"
          >
            Grid
          </button>
        </div>
      </div>

      <form className="history-filters" onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Search by file name..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        <button type="submit">Filter</button>
      </form>

      {error && <p className="error">{error}</p>}
      {rows === null && <p className="hint">Loading…</p>}
      {rows && rows.length === 0 && <p className="hint">No comparisons match yet.</p>}

      <ul className={viewMode === "grid" ? "history-grid" : "history-list"}>
        {rows?.map((row) => (
          <HistoryRow
            key={row.comparison_id}
            row={row}
            onOpenResult={onOpen}
            onDeleted={handleDeleted}
          />
        ))}
      </ul>
    </div>
  );
}

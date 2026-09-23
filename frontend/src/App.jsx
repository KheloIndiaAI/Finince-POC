import { useState } from "react";
import UploadPage from "./pages/UploadPage";
import ReviewPage from "./pages/ReviewPage";
import ResultPage from "./pages/ResultPage";
import HistoryPage from "./pages/HistoryPage";

// The MVP is small enough that plain state beats a router (see
// engineering_doc/coding-standards.md #1: no abstraction until a 2nd use).
export default function App() {
  const [comparison, setComparison] = useState(null); // last ComparisonDetail
  const [view, setView] = useState("upload"); // upload | review | result | history

  // Normal path: upload auto-confirms and jumps straight to the result, no
  // manual review step (per product decision — kept simple on purpose).
  function handleCompleted(detail) {
    setComparison(detail);
    setView("result");
  }

  // Fallback path: only reached when extraction couldn't confidently read
  // both amounts. ReviewPage is kept for exactly this case, not deleted.
  function handleNeedsReview(detail) {
    setComparison(detail);
    setView("review");
  }

  function handleConfirmed(result, summary) {
    setComparison((prev) => ({ ...prev, result, summary, status: "COMPLETED" }));
    setView("result");
  }

  function handleStartOver() {
    setComparison(null);
    setView("upload");
  }

  function handleOpenFromHistory(detail) {
    setComparison(detail);
    setView("result");
  }

  const activeTab = view === "history" ? "history" : "upload";

  return (
    <div className="app">
      <header className="app-header">
        <h1>Sanction vs Expenditure Comparison</h1>
        <p>Upload a sanction letter and its utilization certificate to check spend against approval.</p>
        <nav className="app-nav">
          <button
            className={activeTab === "upload" ? "" : "secondary"}
            onClick={handleStartOver}
          >
            New comparison
          </button>
          <button
            className={activeTab === "history" ? "" : "secondary"}
            onClick={() => setView("history")}
          >
            Past comparisons
          </button>
        </nav>
      </header>
      {view === "upload" && (
        <UploadPage onCompleted={handleCompleted} onNeedsReview={handleNeedsReview} />
      )}
      {view === "review" && comparison && (
        <ReviewPage comparison={comparison} onConfirmed={handleConfirmed} />
      )}
      {view === "result" && comparison && (
        <ResultPage comparison={comparison} onStartOver={handleStartOver} />
      )}
      {view === "history" && <HistoryPage onOpen={handleOpenFromHistory} />}
    </div>
  );
}

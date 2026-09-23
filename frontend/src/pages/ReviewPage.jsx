import { useState } from "react";
import { confirmComparison } from "../api";

export default function ReviewPage({ comparison, onConfirmed }) {
  const extraction = comparison.extraction || {};
  const [sanctionedAmount, setSanctionedAmount] = useState(
    extraction.sanctioned_amount ?? ""
  );
  const [expenditureAmount, setExpenditureAmount] = useState(
    extraction.expenditure_amount ?? ""
  );
  const [expenditureType, setExpenditureType] = useState(
    extraction.expenditure_type || ""
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleConfirm() {
    setBusy(true);
    setError("");
    try {
      const { result, summary } = await confirmComparison(
        comparison.comparison_id,
        {
          sanctioned_amount: sanctionedAmount,
          expenditure_amount: expenditureAmount,
          expenditure_type: expenditureType,
        }
      );
      onConfirmed(result, summary);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card">
      <h2>Review the extracted amounts</h2>
      <p className="hint">Check these against the documents, then confirm.</p>

      {extraction.mismatch_note && (
        <div className="warning-banner">
          <strong>These documents may not be a matching pair.</strong>
          <span>{extraction.mismatch_note}</span>
        </div>
      )}

      <label>
        Sanctioned amount (Rs)
        <input
          value={sanctionedAmount}
          onChange={(e) => setSanctionedAmount(e.target.value)}
        />
        {extraction.sanctioned_snippet && (
          <span className="snippet">&quot;{extraction.sanctioned_snippet}&quot;</span>
        )}
      </label>

      <label>
        Expenditure / utilized amount (Rs)
        <input
          value={expenditureAmount}
          onChange={(e) => setExpenditureAmount(e.target.value)}
        />
        {extraction.expenditure_snippet && (
          <span className="snippet">&quot;{extraction.expenditure_snippet}&quot;</span>
        )}
      </label>

      <label>
        Expenditure type
        <input
          value={expenditureType}
          onChange={(e) => setExpenditureType(e.target.value)}
        />
        {extraction.type_snippet && (
          <span className="snippet">&quot;{extraction.type_snippet}&quot;</span>
        )}
      </label>

      {error && <p className="error">{error}</p>}
      <button onClick={handleConfirm} disabled={busy}>
        {busy ? "Comparing..." : "Confirm & Compare"}
      </button>
    </div>
  );
}

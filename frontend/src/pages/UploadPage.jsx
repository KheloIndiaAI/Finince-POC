import { useState } from "react";
import { createComparison, confirmComparison } from "../api";
import Dropzone from "../components/Dropzone";

export default function UploadPage({ onCompleted, onNeedsReview }) {
  const [sanctionFile, setSanctionFile] = useState(null);
  const [expenditureFile, setExpenditureFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    if (!sanctionFile || !expenditureFile) {
      setError("Choose both files.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const detail = await createComparison(sanctionFile, expenditureFile);
      const extraction = detail.extraction;
      const canAutoCompare =
        extraction && extraction.sanctioned_amount != null && extraction.expenditure_amount != null;

      // Straight to the result — no manual confirm step. ReviewPage.jsx is
      // kept (not deleted) as the fallback below, for the one case where we
      // can't safely auto-compare: extraction couldn't confidently read
      // both amounts, so a person has to fill them in before we compute.
      if (!canAutoCompare) {
        onNeedsReview(detail);
        return;
      }

      const { result, summary } = await confirmComparison(detail.comparison_id, {
        sanctioned_amount: extraction.sanctioned_amount,
        expenditure_amount: extraction.expenditure_amount,
        expenditure_type: extraction.expenditure_type || "",
      });
      onCompleted({ ...detail, result, summary, status: "COMPLETED" });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card">
      <h2>Upload both documents</h2>
      <p className="hint">
        Both are read together in one pass — the comparison and summary are generated automatically.
      </p>

      <div className="dropzone-grid">
        <Dropzone label="Sanction Letter" file={sanctionFile} onChange={setSanctionFile} />
        <Dropzone
          label="Expenditure Sheet (UC)"
          file={expenditureFile}
          onChange={setExpenditureFile}
        />
      </div>

      {error && <p className="error">{error}</p>}
      <button type="submit" disabled={busy}>
        {busy ? "Reading documents & comparing..." : "Compare Documents"}
      </button>
    </form>
  );
}

# Architecture

## What the system does
A user uploads two documents — a Sanction Order and its Utilization
Certificate (UC). The system reads both, pulls out the sanctioned amount,
the amount actually spent (utilized), and the type of expenditure, then
tells the user in plain sentences whether the spending matches the sanction
and how much was used.

## MVP-1 scope
IN:
- Upload both files together (2 tabs, one API call).
- Store originals in S3, metadata in Postgres.
- Extract text (AWS Textract for scanned PDFs; direct text for digital PDFs).
- LLM (Claude via Bedrock) picks the fields from the text (amounts, type,
  and any remark on balance handling).
- Python computes difference, utilization %, and status automatically,
  right after extraction — no manual confirm step when both amounts were
  found. The manual review screen still exists and is used only as a
  fallback when extraction leaves an amount blank (person fills it in).
- LLM writes the result as sentences (versioned summary), including the
  UC's balance/refund remark when the document states one.
- React frontend: upload -> result directly (review only when needed) ->
  history.

OUT (later — do not build now):
- Matching many documents to each other.
- One UC covering several quarters/sanctions (segmentation).
- Carry-forward / previous-quarter balance accounting.
- Vector DB / embeddings / semantic search.
- Login, users, and per-user access control.
- DPDP / PII hardening.

## The fields we extract
- sanctioned_amount — from the Sanction Order (the amount sanctioned/granted).
- expenditure_amount — the UTILIZED figure from the UC. NOT the
  grant-received figure, NOT a carried/unspent balance figure.
- expenditure_type — the purpose from the sanction (e.g. staff salary,
  non-recurring grant, sports equipment, one-time grant).
- remarks_snippet — an explicit remark in the UC about what happens to a
  balance or shortfall (refund, release by head office, adjustment
  against a future sanction). Empty when the document doesn't state one;
  never inferred or calculated, only quoted verbatim.
- uc_purpose_snippet — for a UC that breaks expenditure down by category
  (a table with several rows: "Strength & Conditioning", "Physiotherapy",
  "Sports Equipment", etc.), the specific category/categories the actual
  non-zero spend was recorded against, quoted verbatim. Lets a reviewer see
  when money moved under only part of the sanctioned purpose. Empty when
  there's no such breakdown.
Store the raw source snippet for each field, for traceability.

TABLE-SHAPED UCs: a UC is often a table with several category rows and a
Total row (Amount Received / Expenditure incurred / Balance columns). The
extraction prompt is told to read the Total row's Expenditure column, never
to sum the category rows itself (no LLM arithmetic) — if there's no visible
Total row, expenditure_amount comes back null and the person fills it in on
the review screen rather than getting a guessed number.

## Flow diagram
```mermaid
flowchart TD
    A[User uploads Sanction PDF + UC PDF] --> B[POST /api/comparisons]
    B --> C[Store both originals in S3]
    C --> D["Extract text (pdfplumber, or Textract if scanned)"]
    D --> E["Claude (Bedrock) picks fields:\nsanctioned_amount, expenditure_amount,\nexpenditure_type, remarks_snippet"]
    E --> F{Both amounts found?}
    F -- Yes --> G["Frontend auto-calls\nPOST /confirm with extracted values"]
    F -- No --> H[Review screen: person fills in\nthe missing amount, then confirms]
    H --> G
    G --> I["Python computes:\ndifference, utilization %, status"]
    I --> J["Claude writes the plain-English\nsummary (versioned)"]
    J --> K[Result screen: stats, snippets,\nremark callout, summary]
    K --> L[("Postgres: comparisons,\ndocuments, extraction,\nresult, summaries")]
    K --> M["Past comparisons list\n(GET /api/comparisons)"]
    M --> N[Expand a row: view original\nPDFs (presigned S3 URL) + summary]
    M --> O["Delete a row\n(DELETE /api/comparisons/{id})"]
    O --> P[Removes all DB rows + both\nS3 originals for that comparison]
```

## Flow (happy path)
1. POST /api/comparisons (sanction_file + expenditure_file)
   -> create comparison_id, upload both to S3, save documents,
      extract text, LLM picks the fields.   Status: EXTRACTED
2. If both amounts were found: the frontend calls confirm right away
   with the extracted values (no separate endpoint for this — same
   POST /api/comparisons/{id}/confirm below, just called automatically
   instead of waiting on a person) -> Python computes result, LLM
   writes summary v1.   Status: COMPLETED. User lands on the result
   screen directly. Otherwise, the frontend falls back to the review
   screen so a person can fill in the missing amount(s), then:
3. POST /api/comparisons/{id}/confirm (manual path only)
   -> Python computes result, LLM writes summary v1.   Status: COMPLETED
4. GET /api/comparisons/{id} -> files, extraction, result, current summary.
5. POST /api/comparisons/{id}/summary/regenerate
   -> new summary version, marked current; old versions kept.
6. GET /api/comparisons/{id}/summaries -> full version history.
7. GET /api/comparisons -> history list (?q=, ?date_from=, ?date_to=), newest
   first: file names, created_at, and result summary if confirmed. Backs the
   frontend's "Past comparisons" tab; every comparison is kept, none deleted.
8. Each document in a comparison's response carries a short-lived presigned
   S3 view_url (storage.presigned_url), so the frontend can link straight to
   the original PDF without proxying the file through the backend.
9. DELETE /api/comparisons/{id} -> deletes every row tied to that
   comparison_id (documents, document_content, extraction, result, every
   summary version, the comparison itself) and both S3 originals.
   Irreversible. Used by the "Delete" action on the history list.

## Status values
CREATED -> PROCESSING -> EXTRACTED -> COMPARING -> COMPLETED.  FAILED on error.

## Comparison rules (Python only, see services/comparison.py)
- difference      = sanctioned_amount - expenditure_amount
- utilization_pct = expenditure_amount / sanctioned_amount * 100  (guard /0)
- overall_status:
    FULLY_UTILIZED   expenditure == sanctioned
    UNDER_UTILIZED   expenditure <  sanctioned
    OVER_UTILIZED    expenditure >  sanctioned
  (a tolerance band can be added later; MVP uses exact compare)

## Data model (Postgres, all linked by comparison_id)
- comparisons             one row per comparison (id, status).
- documents               the two uploaded files (type SANCTION|UC, s3_key, size).
- document_content        extracted text per document (+ extraction_method).
- comparison_extractions  the 3 picked fields + source snippets (editable pre-confirm).
- comparison_results      computed totals, difference, utilization %, status.
- comparison_summaries    versioned sentence summaries (is_current marks the latest).
Types are dialect-agnostic (Uuid, Numeric, JSON) so tests run on SQLite.
Full column-by-column detail, keys, and the ER diagram: `engineering_doc/schema.md`.

## Known document variety (why the extraction prompt is dynamic, not templated)
The real sanction/UC files vary a lot more than one clean template:
- Formats: a narrative GFR-12C paragraph, a GFR-12C table, a settlement
  letter with its own table, or a covering letter bundling a forwarded
  email and a scanned attachment — all as "the UC".
- Language: English, Hindi, or mixed in the same PDF.
- Direction: expenditure can be under, equal to, OR over the sanctioned
  amount (a real Tripura case had 20% over-spend).
- Bundling: one UC file can carry more than one quarter/sanction reference.
  For MVP-1 the prompt is told to prefer the figures matching the sanction
  order's own reference/date, and to return null rather than guess when it
  can't tell — segmentation into separate quarters is still explicitly OUT
  of scope (see above), this is just "don't silently pick the wrong one".
- OCR risk: AWS Textract's DetectDocumentText is strongest on Latin script;
  a Hindi-only UC may extract poorly. This is a known limitation, not yet
  solved — if Hindi documents turn out to be common, revisit the OCR engine
  (e.g. Textract's newer multilingual support) rather than trying to fix it
  in the prompt.

## Tech stack
- Backend: Python 3.10, FastAPI, SQLAlchemy, Postgres.
- Frontend: React on Node.js (separate app in frontend/). Backend enables
  CORS for the dev server.
- AWS S3 (originals + generated summary files), region ap-south-1.
- OCR: AWS Textract (async, reads the file straight from S3) for scanned
  PDFs; pdfplumber for digital PDFs with a text layer.
- LLM: Claude Sonnet via AWS Bedrock (Converse API), model id from env
  (CLAUDE_MODEL).
- Config from environment via pydantic-settings.

## Folders
  backend/app/            application code (one job per file)
  backend/app/api/        FastAPI routers (comparisons.py, results.py)
  backend/app/services/   storage.py (S3), text_extraction.py,
                           field_extraction.py, llm.py, prompts.py,
                           comparison.py, summary.py, summary_pipeline.py,
                           extraction_pipeline.py
  backend/prompts/        LLM prompts, one file per prompt, versioned
  backend/tests/          tests + shared fixtures (conftest.py)
  frontend/               React app

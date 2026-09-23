You are reading two government financial documents for a Sanction vs
Utilization Certificate (UC) comparison: a Sanction Order, and the paperwork
that reports how that sanction was spent. That second document is not always
a clean GFR-12C form — it may be a settlement letter, a fund-adjustment
letter, a covering letter with a table, a multi-category expenditure table,
or even a forwarded email with an attachment. Read the whole text of both
documents, not just the first paragraph — the right figures can be anywhere,
including inside a table.

Return ONLY a JSON object — no other text, no markdown fences.

WHAT TO LOOK FOR:

1. sanctioned_amount — the amount sanctioned/granted/released in the
   SANCTION ORDER text. Usually near "sanction of", "Gross Amount", "Net
   Amount Payable", or a rupee figure followed by its amount in words.

2. expenditure_amount — the amount actually spent, claimed, or settled
   against that sanction, as stated in the UC/settlement text. This is NOT
   the amount that was released/sanctioned, and NOT an unspent or carried
   balance. Look for wording such as: "has been utilized/utilised",
   "utilized for", "expenditure claimed as per UC", "UC settled as per
   norms", "expenditure incurred", "admissible amount". Expenditure can be
   less than, equal to, or MORE than the sanctioned amount — real cases
   include over-spend; do not assume it must be lower.

   TABLE FORMAT — a breakdown table with several category/particular rows
   (e.g. "Strength & Conditioning", "Physiotherapy", "Sports Equipment"
   with sub-items, "One Time Grant") and columns such as "Amount Received",
   "Expenditure incurred"/"Utilized", and "Balance": do NOT read a single
   category row's figure as the answer, and do NOT add the rows up
   yourself (no arithmetic — only report a number that is already written
   somewhere in the document). Instead, find the "Total" or "Grand Total"
   row at the bottom of the table and report the figure from ITS
   "Expenditure incurred"/"Utilized" column. If the table has no visible
   Total row, return null for expenditure_amount rather than summing the
   rows yourself.

3. expenditure_type — what the money was for, from the Sanction Order (e.g.
   "staff salary" / "manpower salary", "non-recurring grant", "sports
   equipment", "one-time grant", "hiring of manpower").

4. uc_purpose_snippet — from the SAME breakdown table (or narrative) in the
   UC/settlement document, which specific category/particular(s) the actual
   non-zero expenditure was recorded against (e.g. "Sports Equipment:
   Rowing", or "Staff salary — Q2"). This lets a reviewer see whether money
   was actually spent under the purpose the sanction named, or only under
   part of it. Quote the row label(s) verbatim, comma-separated if more
   than one category has non-zero expenditure. If the document has no such
   per-category breakdown (a single lump expenditure figure with one
   purpose), return "".

5. remarks_snippet — any explicit remark in the UC/settlement document about
   what happens to a balance or shortfall amount: for example that an
   unspent balance is to be refunded/returned/adjusted, or that an
   over-spent amount is to be released/reimbursed by head office (e.g. "Rs.
   X to be released by SAI HO New Delhi"), or a note about adjustment
   against a future sanction. Copy the exact sentence or line verbatim, in
   whatever language it appears. This is a plain quote, not a calculation —
   if the document does not say anything about balance handling, return "".

DOCUMENTS MAY BE IN HINDI, ENGLISH, OR A MIX. Read both; report amounts as
plain numbers regardless of language. Text may also be noisy or reordered
(scanned copies, prior OCR, multi-column layouts, or a screenshot of an
email) — read past garbled words and find the numbers and their labels.

MULTIPLE SANCTIONS OR QUARTERS IN ONE DOCUMENT: some paperwork bundles
several quarters or several sanction references together (e.g. a covering
letter for Q4 + Q1, or a chain of correspondence). If more than one
sanction/UC pairing is present, prefer the figures whose reference number,
file number, or date matches the SANCTION ORDER TEXT given below. If you
cannot confidently match a figure to this specific sanction, return null for
that field rather than guessing — a person reviews every field before it is
used, so an honest "not found" is far better than a wrong number.

Do not calculate or convert anything (no adding balances, no summing table
rows, no percentages, no currency conversion). Only read values exactly as
written, as plain numbers (no commas, no symbols, no "Rs.").

For each amount/type field, also return the exact source line/snippet you
took it from, in whatever language it appears.

If a value is not found, use null for an amount and "" for text.

Return exactly this JSON shape and nothing else:
{
  "sanctioned_amount": <number or null>,
  "sanctioned_snippet": "<text>",
  "expenditure_amount": <number or null>,
  "expenditure_snippet": "<text>",
  "expenditure_type": "<text>",
  "type_snippet": "<text>",
  "uc_purpose_snippet": "<text or empty string>",
  "remarks_snippet": "<text or empty string>"
}

SANCTION ORDER TEXT:
[[SANCTION_TEXT]]

UTILIZATION / EXPENDITURE DOCUMENT TEXT:
[[UC_TEXT]]

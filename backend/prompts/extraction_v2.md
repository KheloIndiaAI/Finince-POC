You are reading two government financial documents for a Sanction vs
Utilization Certificate (UC) comparison: a Sanction Order, and the paperwork
that reports how that sanction was spent. That second document is not always
a clean GFR-12C form — it may be a settlement letter, a fund-adjustment
letter, a covering letter with a table, or even a forwarded email with an
attachment. Read the whole text of both documents, not just the first
paragraph — the right figures can be anywhere, including inside a table.

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

3. expenditure_type — what the money was for, from the Sanction Order (e.g.
   "staff salary" / "manpower salary", "non-recurring grant", "sports
   equipment", "one-time grant", "hiring of manpower").

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

Do not calculate or convert anything (no adding balances, no percentages,
no currency conversion). Only read values exactly as written, as plain
numbers (no commas, no symbols, no "Rs.").

For each field, also return the exact source line/snippet you took it from,
in whatever language it appears.

If a value is not found, use null for an amount and "" for text.

Return exactly this JSON shape and nothing else:
{
  "sanctioned_amount": <number or null>,
  "sanctioned_snippet": "<text>",
  "expenditure_amount": <number or null>,
  "expenditure_snippet": "<text>",
  "expenditure_type": "<text>",
  "type_snippet": "<text>"
}

SANCTION ORDER TEXT:
[[SANCTION_TEXT]]

UTILIZATION / EXPENDITURE DOCUMENT TEXT:
[[UC_TEXT]]

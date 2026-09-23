You extract three fields for a government Sanction vs Utilization Certificate (UC)
comparison. Read the two documents below and return ONLY a JSON object — no other text.

Fields to return:
- sanctioned_amount: the amount sanctioned in the Sanction Order, as a plain number in
  rupees (no commas, no symbols).
- expenditure_amount: from the UC, the amount that was UTILIZED / spent. This is the
  "a sum of Rs. X has been utilized" figure. It is NOT the grant-received/sanctioned
  figure and NOT the unspent balance.
- expenditure_type: the purpose/type of the spend from the Sanction Order, e.g.
  "staff salary", "non-recurring grant", "sports equipment", "one-time grant".
- For each field, also return the exact source line/snippet you took it from.

If a value is not found, use null for an amount and "" for text.
Do not calculate anything. Only read the values as written.

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

UTILIZATION CERTIFICATE TEXT:
[[UC_TEXT]]

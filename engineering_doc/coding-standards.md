# Coding Standards

Read alongside architecture.md and local-setup.md in this folder. Root
CLAUDE.md is the index that points here.

## Principles (non-negotiable)
1. Simplest solution that works. No abstraction until there is a second use.
2. One responsibility per file. Files <= 150 lines, functions <= 30 lines.
3. No dead code: no commented-out code, no unused functions, no scratch files
   in app/. If two versions of the same thing exist (e.g. two storage
   helpers), delete one immediately — don't leave both "for now".
4. LLM never does arithmetic. Python computes every number. The LLM only
   reads text and writes sentences.
5. Money is Decimal (rupees) — never float.
6. Secrets live only in .env (git-ignored). Never commit, print, or log a
   secret.
7. Every record links back to one comparison_id.

## Prompt rules
- Every LLM prompt is a separate file in backend/prompts/, named
  <purpose>_v<N>.md.
- Code loads the prompt by name; the version string is stored with each
  extraction/summary (prompt_version).
- Change a prompt = new file + bump version. Never edit a shipped prompt in
  place. Old prompt versions are kept on disk (extraction_v1.md,
  extraction_v2.md, ...) as an audit trail of what produced past results —
  this is different from principle 3 (no dead code): a duplicate *module*
  doing the same job gets deleted, but a superseded prompt *version* stays,
  because comparison_extractions.prompt_version can point back to it.

## Testing rules
- New behaviour ships with at least one test.
- Stub the boundaries (S3, Textract, Bedrock) — tests never call AWS. Use the
  shared fixtures in backend/tests/conftest.py (`client`, `session_factory`,
  `uploaded`) instead of re-wiring a test app per file.
- Pure logic (comparison math, amount parsing) gets a plain unit test with no
  fixtures at all — see tests/test_comparison.py.

## Amount parsing
Government figures show up as "Rs. 24,42,365/-", "67,35,600", or a bare
number. Match the first run of digits (Indian grouping included) rather than
stripping non-digit characters — stripping lets a leading "Rs." supply a
decimal point that was never there. See field_extraction.py `_to_decimal`.

## Definition of done (each step)
- Code runs. New behaviour has at least one test. No secret in the diff.
- Files/functions within the size limits above.
- No duplicate module doing the same job under two names.
- README.md / local-setup.md updated if the run steps changed.

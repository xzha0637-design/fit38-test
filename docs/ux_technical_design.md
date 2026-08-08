# UX and Technical Design Choices

## UX choices

- Evidence is shown in sequence: source preview, completeness, model result,
  explanation/uncertainty, then human decision.
- Risk uses text labels as well as colour; “Triage evidence, not a verdict”
  remains visible.
- Insufficient data never shows a risk band but still permits human follow-up.
- Status regions use `aria-live`; primary fields have explicit labels; the page
  has a keyboard skip link and semantic result-table headers.
- Retry and Start new assessment are explicit. Reset clears hidden decision and
  follow-up state rather than only hiding panels.
- The first view states the account-review purpose and keeps a Model Information
  link visible before any assessment. Model Information leads with ordinary
  guidance and keeps the exact technical record collapsed until requested.
- Returning from Model Information restores and focuses the current result in
  the same tab; Start new assessment clears it.
- Batch errors remain on their source row and never block valid rows.
- Filter state and matching count are visible; clearing uses the existing
  in-memory results and restores input order.

## Technical choices

- FastAPI and Pydantic provide versioned validation/error contracts.
- A tracked offline adapter prevents dependency on a live platform or secrets.
- XGBoost and SHAP artifacts are versioned and loaded rather than replaced by
  placeholder scores.
- Completeness and scoring share one deterministic feature pipeline.
- Single and batch assessment call the same orchestration path.
- Browser filtering uses cloned arrays and a pure JavaScript module verified
  under Node, protecting source scores and decision fields.
- SQLite persists only expiring minimal assessment context and pseudonymous
  decision/follow-up records. One versioned, schema-validated browser snapshot
  of the displayed whitelisted assessment and visible review state supports
  return navigation and is cleared on reset or tab-session end.
- Browser requests use one JSON client with a bounded timeout, safe non-JSON
  handling and controlled network messages. Follow-up controls expose a busy
  state and prevent duplicate requests.

Trade-offs and scientific limitations are recorded in
`docs/known_limitations.md` and `/model-information`.

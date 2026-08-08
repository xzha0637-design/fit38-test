# Data contract

## Account input

`POST /api/v1/intake`

```json
{
  "identifier": "@DeFotis"
}
```

The endpoint removes one optional `@`, normalises case, validates supported
characters, and resolves the value against the offline fixture index. It returns
one canonical account reference and does not score or retain a raw profile.

The first three selector records are label-free static rows from the two tracked
project datasets. The demo endpoint returns their safe selector metadata but
never returns the source training label.

`POST /api/v1/assessments`

```json
{
  "platform": "x",
  "account_id": "2244994945"
}
```

The backend accepts a validated offline demonstration identifier. No
authentication token or live platform payload is accepted.

## Assessment output

The response schema is defined by `AssessmentResponse` in
`backend/app/schemas.py`. It contains a pseudonymous assessment reference,
completeness, optional model result, explanation factors, recommendation, and
human-oversight warning. Raw account profiles are excluded.

## Contract versions

- API path version: `v1`
- Application version: `0.1.0`
- Model contract: `xgb-offline-v1`
- Threshold contract: `threshold-v1`

Any later interface change must update this document, the relevant schema tests,
and the corresponding stage handover.

## Public account preview

`GET /api/v1/accounts/{account_id}/preview` returns an explicit `source_data`
object with three approved groups: profile, activity, and network. Missing source
values remain JSON `null` and are also listed by a plain-language label. Scenario
metadata, training labels, and internal model features are excluded.

## Feature completeness

`GET /api/v1/accounts/{account_id}/completeness` calculates availability across
the versioned 12-feature model input. A value below `0.5` returns `Insufficient
data`; exactly `0.5` is eligible. Missing features are plain-language labels, and
the response deliberately carries no risk band.

## Scored assessment

Eligible accounts submitted to `POST /api/v1/assessments` receive both the raw
0–1 probability and an analyst-facing integer `risk_score` from 0–100. The
response includes exactly one title-cased band label, model version, threshold
version, ISO-8601 time, and the required non-verdict disclaimer. A scoring
failure returns a retryable error object with no partial score fields.

## Batch assessment

`POST /api/v1/batch-assessments` accepts JSON containing the original `.csv`
filename and text content. The CSV header must be exactly `account_id` and the
limit is 100 data rows. `BatchUploadResponse` includes total, completed and
failed counts plus one ordered `BatchRowResult` per input row. Invalid,
duplicate and unavailable rows have `processing_status: "failed"` and do not
prevent other rows from completing. Raw CSV content is not persisted.

## Human decision and follow-up

`POST /api/v1/assessments/{assessment_id}/decision` records confirm or override;
override requires a reason. `PUT /api/v1/assessments/{assessment_id}/follow-up`
requires an authorised `X-Project-Role` and can flag, update or clear a record.
Both contracts explicitly acknowledge that no platform action occurred.

SQLite is restricted to `assessment_contexts`, `decision_feedback` and
`follow_up_records`. The first table retains only expiring model/recommendation
context for 24 hours so a displayed assessment remains actionable across a
local service restart. The other tables contain pseudonymous assessment
references, model version, workflow state, reason and timestamp. Raw profile,
account identifier and uploaded CSV fields are excluded from all three tables.

New assessment references use the full `asmt_` plus 32 hexadecimal UUID
characters. The API continues accepting the earlier eight-character references
so an existing Iteration 1 record does not break during the transition.

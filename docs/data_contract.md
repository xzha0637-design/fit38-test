# Data contract

## Account input

`POST /api/v1/intake`

```json
{
  "identifier": "@civic_updates"
}
```

The endpoint removes one optional `@`, normalises case, validates supported
characters, and resolves the value against the offline fixture index. It returns
one canonical account reference and does not score or retain a raw profile.

`POST /api/v1/assessments`

```json
{
  "platform": "x",
  "account_id": "2244994945"
}
```

The Stage 00 backend accepts a numeric, offline demonstration account identifier.
No authentication token or live platform payload is accepted.

## Assessment output

The response schema is defined by `AssessmentResponse` in
`backend/app/schemas.py`. It contains a pseudonymous assessment reference,
completeness, optional model result, explanation factors, recommendation, and
human-oversight warning. Raw account profiles are excluded.

## Contract versions

- API path version: `v1`
- Application version: `0.1.0`
- Model contract: `model-contract-v1`
- Threshold contract: `threshold-contract-v1`

Any later interface change must update this document, the relevant schema tests,
and the corresponding stage handover.

## Public account preview

`GET /api/v1/accounts/{account_id}/preview` returns an explicit `source_data`
object with three approved groups: profile, activity, and network. Missing source
values remain JSON `null` and are also listed by a plain-language label. Scenario
metadata, training labels, and internal model features are excluded.

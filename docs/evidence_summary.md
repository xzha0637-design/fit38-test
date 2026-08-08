# Iteration 1 Evidence Summary

## MVP outcome

The Release Candidate implements all 12 agreed User Stories as a cumulative,
offline FastAPI and browser MVP. It provides validated single and CSV-batch
Twitter/X account triage, versioned model output, explainability, model
limitations, human decisions, follow-up review, protected persistence and
non-mutating result exploration.

The system never connects to Twitter/X and contains no moderation or enforcement
integration.

## Acceptance evidence

| User Story | Delivered evidence |
|---|---|
| US1.1 | Normalised account intake, controlled validation and representative selector |
| US1.2 | Whitelisted public preview, explicit nulls and source/model separation |
| US1.3 | Controlled error states, retry and stale-state-free reset |
| US2.1 | 12-feature completeness with inclusive 50% boundary |
| US2.2 | Real `xgb-offline-v1` artifact, versioned bands and deterministic results |
| US3.1 | Ordered top-three SHAP factors and explicit uncertainty |
| US3.2 | Directly linked model card with verified metrics and required limitations |
| US4.1 | Confirm/override reason workflow and no-action acknowledgement |
| US4.2 | Minimal pseudonymous SQLite records, safe logs and role-limited reads |
| US4.3 | Authorised flag/update/clear workflow for completed or insufficient results |
| US5.1 | Documented CSV validation, row-level failures, partial success and counts |
| US5.2 | Risk sorting, three filters, visible state/count and clear without rerun |

Automated mapping for every AC is maintained in `docs/test_mapping.md`.

## Repository evidence

The cumulative GitHub delivery branches preserve one stage-specific commit each:

| Stage | Branch | Commit |
|---:|---|---|
| 00 | `stage/00-project-scaffold` | `504e5b9` |
| 01 | `stage/01-us1.1-account-intake` | `75cc437` |
| 02 | `stage/02-us1.2-account-preview` | `a9c47a0` |
| 03 | `stage/03-us2.1-completeness` | `67e6311` |
| 04 | `stage/04-us2.2-risk-scoring` | `60319b5` |
| 05 | `stage/05-us3.1-explanation-uncertainty` | `5849015` |
| 06 | `stage/06-us4.1-confirm-override` | `3ea208e` |
| 07 | `stage/07-us1.3-recovery-reset` | `7ee6201` |
| 08 | `stage/08-us4.2-data-protection` | `49e6e85` |
| 09 | `stage/09-us4.3-follow-up` | `23ffe5d` |
| 10 | `stage/10-us3.2-model-information` | `529272f` |
| 11 | `stage/11-us5.1-batch-assessment` | `e42c1cd` |
| 12 | `stage/12-us5.2-sort-filter` | `86a55ca` |

Stage 13 adds the final integration commit on
`stage/13-integrated-mvp-rc1`.

## RC quality result

- Automated regression: **86 passed, 0 failed**
- Repeatable Run Sheet: **PASS**
- JavaScript syntax: **PASS**
- Open critical/high defects: **0**
- `git diff --check`: recorded in the Stage 13 handover after final review
- Privacy: only expiring pseudonymous assessment context and approved
  decision/follow-up tables persist
- Accessibility: labelled primary inputs, keyboard skip link, live status
  regions, semantic table headers and text risk labels
- Batch/single consistency: same fixture produces the same status, score and band

Known scientific and product limitations remain explicit in
`docs/known_limitations.md` and the directly linked model information page.

# Iteration 1 Product Backlog

All stories below are **Completed** in RC1. Full automated evidence is linked by
AC in `docs/test_mapping.md`.

| Story | User value and Acceptance Criteria summary | Primary owner | Delivery branch |
|---|---|---|---|
| US1.1 Account intake | Validate/normalise one identifier; controlled invalid/unknown states; representative deterministic scenarios; accessible loading/labels | Wei Zhang | `stage/01-us1.1-account-intake` |
| US1.2 Account preview | Show approved profile/activity/network source fields; preserve and name missing values; exclude internal labels/features; separate source from model output | Wei Zhang | `stage/02-us1.2-account-preview` |
| US1.3 Recovery/reset | Controlled source/model/malformed/unknown errors; retry or start new; clear stale state; restore focus | Keliang Chen | `stage/07-us1.3-recovery-reset` |
| US2.1 Completeness | Calculate/display completeness before scoring; below 50% is Insufficient; 50% is eligible; name missing features | Keliang Chen | `stage/03-us2.1-completeness` |
| US2.2 Risk scoring | Real versioned model and thresholds; exactly one band; model/time shown; deterministic; accessible non-verdict result; controlled failure | Xianze Zhang | `stage/04-us2.2-risk-scoring` |
| US3.1 Explanation/uncertainty | Up to three ordered plain-language factors with direction/value; common assessment/version context; uncertainty and safe degraded explanation state | Zhongyao Zhang | `stage/05-us3.1-explanation-uncertainty` |
| US3.2 Model limitations | Scope, schema, versions, datasets, metrics/evidence/date; graph/shift/drift/false-positive risks; enforcement prohibition; direct result links | Xianze Zhang | `stage/10-us3.2-model-information` |
| US4.1 Confirm/override | Human decision after assessment; override reason; minimal record; no platform action; acknowledgement and duplicate prevention | Yetong Zhang | `stage/06-us4.1-confirm-override` |
| US4.2 Data protection | No raw profile persistence; safe logs; minimal pseudonymous tables; authorised feedback read | Yetong Zhang | `stage/08-us4.2-data-protection` |
| US4.3 Follow-up | Completed/insufficient results can be flagged, updated or cleared with reason by an authorised role; minimal record; no action | Zhongyao Zhang | `stage/09-us4.3-follow-up` |
| US5.1 Batch assessment | Exact documented CSV; file/header/limit/duplicate/identifier validation; row-level partial success; visible counts; no action | Mingyu Xu | `stage/11-us5.1-batch-assessment` |
| US5.2 Sort/filter | Sort risk; filter band/completeness/review status; show active state/count; clear without rerun; never mutate score/decision | Mingyu Xu | `stage/12-us5.2-sort-filter` |

Definition of Ready used: user value, scope, AC, dependencies, test expectations,
offline fixtures and privacy/human-oversight constraints were known before Build.

Definition of Done used: implementation, mapped automated tests, regression,
README/technical documentation, stage handover, Git commit and ZIP snapshot were
complete.

# Iteration 1 MVP Definition

## Goal

Provide a small, reliable, offline tool that helps an external social media
safety analyst prioritise public Twitter/X account evidence for human review.

## Included

- validated single-account intake and public-data preview;
- a 12-feature completeness gate with Insufficient data handling;
- deterministic `xgb-offline-v1` Low/Medium/High risk assessment;
- ordered SHAP factors, uncertainty and a directly linked model card;
- confirm/override and authorised follow-up workflows;
- minimal pseudonymous SQLite persistence;
- validated CSV batches of up to 100 rows with partial success;
- local sorting/filtering without rerunning or mutating results;
- controlled errors, reset/recovery and an accessible browser interface.

## Excluded

- live Twitter/X access, private data or credentials;
- full follower/following graphs and content-semantic inference;
- automated moderation, reporting, suspension or enforcement;
- claims that a result proves automation, harm, fraud or a policy violation;
- independent external-dataset validation and formal probability calibration.

## Success gates

- all 12 User Stories meet their Acceptance Criteria;
- the same validated fixture and model version return the same score and band;
- no risk result is produced below 50% completeness;
- raw account profiles and uploaded CSV content are not persisted;
- every automated test and the Run Sheet pass;
- no critical or high defect remains open.

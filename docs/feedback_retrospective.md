# RC Feedback and Retrospective

## Engineering feedback incorporated

- A decorative non-ASCII status separator was not portable across the Windows
  test process; status text now uses an ASCII separator.
- Treating a missing score numerically made ascending results misleading; null
  scores now remain after scored results.
- Hiding a panel is not sufficient reset behaviour; all follow-up fields and
  acknowledgements are explicitly cleared.
- New batch work should not inherit prior filters; controls and the source cache
  reset before each upload.
- Operational instructions must be executed, not only reviewed; the Run Sheet
  now has a repeatable module command.

## What worked

- Story-sized cumulative branches produced a clear contribution history.
- Acceptance tests before each implementation kept scope narrow.
- Offline fixtures made Low/Medium/High, insufficient and error demos stable.
- Minimal persistence and no-action wording remained consistent across features.

## Improvement actions for Iteration 2

- Add independent external-dataset evaluation and formal calibration evidence.
- Add browser-level automated accessibility testing in addition to static checks.
- Replace the demonstration role header with the project’s approved identity and
  authorisation mechanism before any non-local deployment.
- Define product analytics that do not collect raw profile data.
- Record team/member feedback and Trello evidence links after the live review.

The final team retrospective should append participant comments without removing
this verified RC engineering record.

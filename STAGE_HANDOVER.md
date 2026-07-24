# Stage handover

- **Stage:** 12 — US5.2 Sort and Filter
- **Primary owner:** Mingyu Xu
- **Branch:** `stage/12-us5.2-sort-filter`

Returned batch results can be sorted by risk score and filtered by risk band,
completeness state and review status. Active controls and matching count remain
visible. Clear restores the original row order using the existing in-memory
results; filtering does not fetch, rerun, mutate scores or alter decision data.
Rows without a risk score remain after scored rows in either sort direction.

All AC1–AC4 map to four tests in `docs/test_mapping.md`.

- **Executed:** 57 automated tests in 4.68 seconds.
- **Passed:** 57.
- **Failed:** 0.

Stage 13 performs final integration, regression and release-candidate evidence.

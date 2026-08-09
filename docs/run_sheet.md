# Iteration 2 Run Sheet

## Preconditions

- Work from the repository root.
- Use Python 3.10 in the `fit5238-backend` Conda environment.
- No Twitter/X credential, network connection, or `.env` secret is required.
- Confirm `models/xgb-offline-v1/` contains the tracked runtime artifacts.

## Automated release check

Run:

```powershell
python -m scripts.verify_run_sheet
```

Expected final line:

```text
RUN SHEET PASS: offline shell, model info, health, single and batch paths
```

Then run:

```powershell
python -m pytest --basetemp ".pytest-tmp"
```

Expected RC result: every collected test passes with zero failures.

## Start and stop

Start the service:

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000/>. Confirm the offline demonstration badge and
human-oversight notice are visible. Stop with `Ctrl+C`.

## Manual smoke sequence

1. Select **High example — @everyletterbot (project dataset)** and begin the assessment.
2. Confirm source preview, completeness, High risk result, top factors,
   uncertainty and the model-information link appear.
3. Open model information. Confirm the ordinary-language sections appear first;
   expand the technical record and confirm `xgb-offline-v1`, `threshold-v1`,
   evaluation evidence, limitations and the enforcement prohibition.
4. Return and confirm the same 91 / 100 High result and suggested human-review
   priority remain. Record an Override with
   a reason, then flag the assessment for
   follow-up. Confirm both acknowledgements state that no platform action
   occurred.
5. Start a new assessment. Confirm old decision and follow-up state is absent.
6. Download the CSV template, add one invalid row, and upload it.
7. Confirm valid rows complete, the invalid row fails independently, and the
   completed/failed counts remain visible.
8. Sort by highest risk and apply each filter. Confirm active filters and
   matching count are visible. Clear filters and confirm original row order
   returns without another processing message.

## Controlled failure checks

- Blank or malformed identifiers show validation guidance.
- An unknown offline account shows a controlled unavailable state.
- A non-CSV file, file above 100 KB, wrong header, or more than 100 rows is rejected.
- Removing a required model artifact makes `/api/v1/health` degraded and blocks
  scoring rather than presenting a placeholder score.

No step contacts Twitter/X or triggers reporting, moderation, suspension, or
another platform action.

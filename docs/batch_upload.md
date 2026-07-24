# Batch upload

Use the downloadable `frontend/batch-upload-template.csv` file.

- File extension: `.csv`
- Header: exactly `account_id`
- Row limit: 100 account rows, excluding the header
- Identifier format: 1–32 letters, numbers or underscores; an optional leading
  `@` is accepted and removed
- Duplicate comparison: case-insensitive after identifier normalisation

The server validates rows in file order. An invalid, duplicate, or unavailable
offline identifier is reported on its own row and does not prevent other valid
rows from being assessed. Completed and failed counts remain visible in the
browser while the batch is processing and after it completes.

Processing uses only bundled offline fixtures. Uploading a batch cannot contact
Twitter/X or trigger moderation, reporting, suspension, or any other platform
action.

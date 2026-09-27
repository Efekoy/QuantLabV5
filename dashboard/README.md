# QuantLab local research dashboard

Run `dashboard\start_dashboard.bat` from the repository root on Windows. The UI opens at http://localhost:3000 and the local API listens at http://127.0.0.1:8000. Python 3.11+ and Node 20+ are required. The script installs dependencies locally, imports V5.4 artifacts, and starts both services. No API key, Docker, cloud service, or authentication is used.

## Layout

- `adapters/`: read-only lab contract and V5.4 importer adapter
- `backend/`: FastAPI, SQLite schema, importer, Git status, and telemetry
- `database/`: dashboard-owned SQLite data (ignored by Git)
- `frontend/`: React, Vite, TypeScript terminal UI
- `runtime/`: optional local telemetry files (ignored by Git)
- `tests/`: API and import checks

Manual import: `set PYTHONPATH=dashboard\.vendor;.` then `python -m dashboard.backend.import_lab --lab v5.4` from the repository root. Re-import is deterministic and preserves notes and collection memberships.

## Publishing live progress from a future lab

Write `dashboard/runtime/current_run.json` atomically with keys `lab`, `stage`, `status`, `evaluated`, `total`, `family`, `operation`, `preliminary_qualifiers`, `elapsed_seconds`, `eta_seconds`, `last_checkpoint`, and `errors`. Append JSON objects to `dashboard/runtime/events.jsonl` with `timestamp`, `kind`, and `message`. The API streams file changes via SSE every two seconds. Supply sealed flags and keep unrevealed scientific metrics out of telemetry. To import scientific results, implement `LabAdapter` and register a new import option; the frontend uses the generic lab model.

The demo replay on the Runs page interpolates between 0, 1M, 5M, 10M, and the recorded V5.4 final specification count. It is labeled as a simulation and does not write scientific files.

## Scientific boundaries

V5.4 metrics and classifications come from frozen local artifacts. The four candidate curves come from recorded discovery trade returns and validation/audit daily returns. The dashboard stores compact summaries plus curves for the four supported candidates; it does not duplicate the large raw row files. Notes, watchlist, and collections live only in dashboard SQLite. No research code or frozen artifact is edited.

## Current scope

Only V5.4 has a scientific artifact adapter and imported strategy records. V2, V3, V4, V5, and V6 appear as unimported lab placeholders. Full curves are indexed for the four validation-supported candidates; other strategies retain compact metrics and exact specifications. The optional process CPU/RAM monitor is not included. The historical artifacts do not provide a complete timestamped checkpoint series, so demo intermediate milestones are simulated around the recorded final search count. The Vite build currently emits a bundle-size advisory; it still builds and runs normally.

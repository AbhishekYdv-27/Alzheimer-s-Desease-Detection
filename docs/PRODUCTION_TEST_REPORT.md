# Production Test Report

**Run date:** 2026-10-24
**Environment:** Local Windows development workstation; isolated SQLite test database; no public deployment.

## Environment and commands

| Component | Observed version / command |
|---|---|
| Python | `3.13.14` |
| Node.js | `v24.20.0` |
| npm | `11.19.0` |
| FastAPI / PyTorch / Vite | `0.141.1` / `2.13.0` / `6.4.5` |
| Frontend dependencies | React `18.3.1`; React Router DOM `7.18.4`; Tailwind CSS `4.3.3` |
| Backend command | `.\.venv\Scripts\python.exe run_backend.py` |
| Frontend command (from `frontend`) | `npm.cmd run dev -- --host 127.0.0.1 --port 5173` |
| Backend URL | `http://127.0.0.1:8001` |
| Frontend URL | `http://127.0.0.1:5173` |
| API docs | `http://127.0.0.1:8001/docs` |
| Backend database during smoke tests | `%TEMP%\alzheimers-production-audit.sqlite3` (isolated test DB; not the project/user database) |

Both development servers were listening concurrently on loopback interfaces. The backend was restarted after the final settings changes; it logged application startup completion and remained responsive. The frontend server remained active during the backend restart.

## Feature workflow results

| Feature | Test Method | Expected Result | Actual Result | Status | Evidence |
|---|---|---|---|---|---|
| Backend process startup | Started `run_backend.py` with isolated DB and loopback host | Startup completes and process remains listening on port 8001 | Uvicorn started, application startup completed, process remained listening | PASS | Live backend log; listener PID 14608 during final check |
| Backend health | `GET /health` against running server | Healthy response, HTTP 200 | `{"status":"healthy","service":"alzheimers-ai-platform"}`, HTTP 200 | PASS | `curl.exe` live response |
| API health and docs | Registered routes/OpenAPI and earlier local endpoint checks | Actual registered routes resolve; no duplicate operation IDs | Health route registered; unique OpenAPI IDs regression test passes. `/docs` is enabled. | PASS | `test_openapi_operation_ids_are_unique`; actual route inventory |
| Frontend startup and build | Vite local server; `npm.cmd run build` | Server and TypeScript/Vite production build complete | Vite `6.4.5` served on port 5173; latest build transformed 1,597 modules | PASS | Vite startup and build output |
| Frontend lint | `npm.cmd run lint` | No lint errors | Exit 0; 0 errors and 4 warnings (two Fast Refresh export warnings and two hook dependency warnings) | PASS WITH WARNINGS | ESLint output |
| Browser dashboard | Opened authenticated `/dashboard`, then clean reload after Vite HMR | Dashboard loads data and runtime model/dataset status without a fatal error | Dashboard loaded; model availability reflected the backend; dataset displayed “Not bundled”. A transient HMR `useAuth must be used within an AuthProvider` error cleared after full reload; clean reload showed only React Router v7 future-flag warnings. | PASS AFTER RELOAD | Integrated browser accessibility snapshots and console events |
| Browser explainability page | Navigated to `/explainability` after backend restart | Page loads; configured model status comes from actual model readiness | Page loaded and displayed ResNet50 “Checkpoint ready”; no Swin Transformer active claim. | PASS | Integrated browser snapshot after readiness request completed |
| Registration and authenticated session | Local browser registration and authenticated dashboard flow | New account receives token and opens protected UI | Browser registration and dashboard were previously exercised on the isolated test DB. Existing browser token continued to work after a controlled backend restart using the stable development secret. | PASS LOCALLY | Prior browser/API smoke execution; dashboard still authenticated after final backend restart |
| Login and invalid credentials | Automated isolated TestClient flow; browser registration tested separately | Correct credentials issue a token; wrong password is rejected without a token | Registration and valid login returned HTTP 200; wrong password returned HTTP 401 with `Invalid email or password`. Browser invalid-login UX was not exercised. | PASS IN API TESTS; NOT TESTED IN BROWSER | `test_authentication_registration_login_and_invalid_password` |
| Role restrictions and ownership | Backend regression tests and live API checks | Public signup cannot assign doctor; patient-only and owner checks remain enforced | Doctor role input returned HTTP 422; profile role mutation had no effect; cross-user analysis/report and Grad-CAM requests were rejected | PASS IN TESTS AND API SMOKE | `test_production_safety.py`, `test_role_security.py`, live API response checks |
| Frontend-to-backend connectivity | Vite proxy, browser requests, live API requests after server restart | Requests use local API proxy and return valid responses | Local proxy was exercised; `GET /api/models/` returned 200 without redirect; CORS preflight previously returned 200. | PASS LOCALLY | Live server log and browser/API smoke |
| MRI file validation | Authenticated TestClient upload tests for malformed and unsupported bytes | Reject invalid formats and enforce upload limits | Invalid bytes and unsupported GIF are rejected; over-size input returns 413; valid PNG bytes are decoded and saved with a canonical suffix. | PASS IN TESTS | `test_upload_validation_*`, `test_prediction_rejects_unsupported_image_format` |
| MRI upload and inference | Browser uploaded a synthetic image to the local prediction endpoint | Authenticated upload reaches the configured model and returns its real response | Synthetic upload reached the local ResNet50 checkpoint; no inference mock or random-weight substitution was used. | PASS FOR SYNTHETIC SMOKE ONLY | Prior local browser/API execution; local checkpoint `backend/models/resnet50_best.pth` |
| Prediction output | Inference smoke with synthetic input | Output matches four configured labels and probability values are valid | Four configured class outputs returned; probabilities were within range and summed to 1. | PASS FOR SYNTHETIC SMOKE ONLY | Prior isolated inference smoke; registry mapping |
| Grad-CAM generation and display | Authenticated explain request and local browser rendering | Heatmap/overlay are generated, privately retrievable, and aligned to source | Heatmap and overlay were generated and displayed at 224×224; unauthorized asset access was rejected by regression test. | PASS FOR SYNTHETIC SMOKE ONLY | Prior browser/API smoke; `test_gradcam_assets_require_authentication` |
| CLAHE and U-Net segmentation | Inspected active inference path and checkpoint resources | If implemented as active workflow, preprocessing/segmentation execute with valid outputs | CLAHE and U-Net are not in the verified active inference path; no trained U-Net checkpoint was supplied. | BLOCKED / NOT ACTIVE | Inference implementation inspection; no segmentation output claimed |
| Real MRI evaluation | Dataset validator | Authorized real samples cover all four configured classes | Validator reported zero images in each class directory and exited 2. No real MRI was used for this run. | BLOCKED | `scripts/validate_mri_dataset.py`; missing authorized dataset |
| Analysis persistence and report retrieval | Isolated SQLite integration smoke; controlled backend lifecycle restart | Owner's analysis/report persist and remain retrievable | Test account and analysis persisted across the controlled backend restart; analysis/report retrieval was exercised. | PASS IN ISOLATED DB | Prior isolated API smoke; database regression tests |
| Appointments, availability, notifications, and notes | Backend workflow tests | Slot conflicts/status changes and notification ownership behave correctly | Slot conflict, approval/rejection, and notification read-state workflows passed in automated tests. Browser booking/doctor approval was not run in this pass. | PASS IN API TESTS; NOT TESTED IN BROWSER | `test_portal_workflow.py` |
| CORS production behavior | Production configuration tests and local preflight | Production requires explicit HTTPS origins; local allowed-origin preflight succeeds | Production checks are covered by tests; local preflight returned HTTP 200. Actual Vercel origin is not configured or tested. | PASS LOCALLY; HOSTED BLOCKED | `test_cors_preflight_allows_local_frontend`; no production origin |
| Database dependency consistency | `python -m pip check` | No broken installed requirements | “No broken requirements found”, exit 0 | PASS | Command output |
| Frontend dependency audit | `npm.cmd audit` after Vite/React Router/Tailwind updates | No unresolved advisories | Exit 0; 0 vulnerabilities. Previous 7 advisories were addressed with Vite `6.4.5`, React Router DOM `7.18.4`, and Tailwind CSS `4.3.3` plus the Vite plugin. | PASS | npm audit output |
| Hosted Vercel + Render deployment | No credentials or production URLs available | Hosted frontend/backend, CORS, disk, model, and browser behavior verified | No deployment attempted; no production URLs, secrets, persistent disk, or hosted checkpoint were supplied. | NOT TESTED / BLOCKED | No external deployment was performed |

## Regression results

The earlier recorded backend baseline was 7 passing tests. The current suite includes regressions for doctor-role escalation, unverified metrics, checkpoint integrity/provisioning failures, and strict checkpoint class validation.

| Command | Actual result |
|---|---|
| `.\.venv\Scripts\python.exe -m pytest -q` | Exit 0; `34 passed, 54 warnings in 28.70s`. Warnings are existing Pydantic v2 class-config and `datetime.utcnow()` deprecations. |
| `Set-Location frontend; npm.cmd run build` | Exit 0; TypeScript build and Vite `6.4.5` production build completed; 1,597 modules transformed. |
| `Set-Location frontend; npm.cmd run lint` | Exit 0; 0 errors, 4 warnings (two Fast Refresh warnings and two React Hook dependency warnings). |
| `.\.venv\Scripts\python.exe -m pip check` | Exit 0; no broken requirements found. |
| `Set-Location frontend; npm.cmd audit` | Exit 0; 0 vulnerabilities after package updates. |
| `py -3 scripts/validate_mri_dataset.py` | Exit 2; zero images in each of the four configured class folders. |
| `npm.cmd run test` | Not run; `frontend/package.json` does not define a test script. |

## Test-data cleanup

After recording the smoke-test evidence, removed the isolated browser test account and its analysis rows from `%TEMP%\alzheimers-production-audit.sqlite3`, plus the two Grad-CAM files and synthetic PNG created for that account. The unrelated local demo account and all other Grad-CAM files were left untouched. The backend was restarted against the isolated database and health returned HTTP 200; both backend and frontend remain bound to loopback for local use.

## Fixes and current limitations

The code changes and security rationale are summarized in [PRODUCTION_READINESS_AUDIT.md](./PRODUCTION_READINESS_AUDIT.md). Additional deployment and security details are in [PRODUCTION_SECURITY_CHECKLIST.md](./PRODUCTION_SECURITY_CHECKLIST.md).

No real patient image was uploaded to an external service. The model smoke test used synthetic input only. Registry accuracy numbers are unverified metadata, not evaluation evidence. No clinical validation is claimed.

## Manual actions still required

1. Obtain consented, authorized MRI data and perform a reproducible holdout evaluation covering all four labels. No accuracy, calibration, or clinical performance claim is currently justified.
2. Independently verify checkpoint provenance and supply the expected SHA-256 plus a private HTTPS artifact URL/token; then test provisioning in the hosted environment.
3. Configure a Render persistent disk, absolute database/checkpoint paths, strong generated secret, and the exact Vercel HTTPS origin in `CORS_ORIGINS`; repeat hosted smoke checks.
4. Require an authorized staff member to verify professional credentials before using `scripts/provision_doctor.py`; the CLI does not itself validate credentials.
5. Decide and implement retention/deletion, rate limiting, account verification/password recovery, token revocation, monitoring, and tested backup/restore.

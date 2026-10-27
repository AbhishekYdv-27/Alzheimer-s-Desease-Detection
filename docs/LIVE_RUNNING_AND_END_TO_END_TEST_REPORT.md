# Live Running and End-to-End Test Report

> **Current status (2026-10-24):** This document preserves the detailed historical local run recorded below. For the latest audited test results, current regression counts, production blockers, and exact status table, see [PRODUCTION_TEST_REPORT.md](./PRODUCTION_TEST_REPORT.md) and [PRODUCTION_READINESS_AUDIT.md](./PRODUCTION_READINESS_AUDIT.md). In particular, upload validation and authentication behavior have since changed; historical outcomes below are not current API contracts.

**Execution date:** 2026-10-20
**Scope:** Local-only application execution and verification. No public deployment or external patient-data service was used.

## Environment

| Component | Observed environment |
| --- | --- |
| Operating system | Windows |
| Backend Python | Repository `.venv`: Python 3.13.14 |
| Python dependency check | `pip check`: no broken requirements |
| Frontend runtime | Node.js 24.20.0, npm 11.19.0 |
| Frontend | React 18.3.1, TypeScript 5.9.3, Vite 5.4.21 |
| Frontend dependencies | Already installed in `frontend/node_modules`; no install or lockfile change |
| Model | `backend/models/resnet50_best.pth` exists; 282,654,191 bytes |
| Database used for live testing | `%TEMP%\alzheimers-live-check.sqlite3`, selected with `ALZHEIMERS_DB_PATH` |

The live backend bound only to `127.0.0.1:8001`; Vite served on `127.0.0.1:5173`. Port 8000 was already held by Docker/WSL and was not stopped or modified. The Vite proxy in the pre-existing worktree targets port 8001.

## Commands and results

Backend command actually validated:

```powershell
$env:ALZHEIMERS_DB_PATH = Join-Path $env:TEMP 'alzheimers-live-check.sqlite3'
.\.venv\Scripts\python.exe run_backend.py
```

The process started successfully using the project entry point. Startup logged `Application startup complete` and `Uvicorn running on http://127.0.0.1:8001`.

Frontend command actually validated, from `frontend`:

```powershell
npm.cmd run dev
```

Vite reported ready at `http://127.0.0.1:5173/`. Both servers remained running after the checks.

## End-to-end results

| Feature | Test Method | Expected Result | Actual Result | Status | Evidence |
| --- | --- | --- | --- | --- | --- |
| Backend startup and schema initialization | Started `run_backend.py` with an isolated DB | Startup completes and schema is initialized | Startup completed; health returned HTTP 200 | PASS | Backend log; `GET /health` returned `{"status":"healthy","service":"alzheimers-ai-platform"}` |
| API root and OpenAPI | HTTP requests to `/`, `/docs`, `/api/health/` | Existing routes respond | All returned HTTP 200; `/docs` returned Swagger UI HTML | PASS | Local HTTP probes |
| Frontend startup | `npm.cmd run dev` in `frontend` | Vite serves the app locally | Vite ready at `http://127.0.0.1:5173/` | PASS | Vite startup output; browser page loaded |
| Frontend-to-backend proxy | Browser `fetch('/api/health')`, `fetch('/api/models/')`, and authenticated `/api/auth/me` | Requests reach backend at configured proxy port | HTTP 200 for health, model listing, and authenticated user lookup | PASS | Browser Playwright results; backend request log |
| Public home page | Opened `http://127.0.0.1:5173/` | Landing page renders | Page title, navigation, main content, and links rendered | PASS | Browser accessibility snapshot |
| Unsupported accuracy-claim cleanup | Inspected and opened home, Analytics, and Models pages after the UI changes | No unsupported accuracy claim is presented as verified performance | Home page now shows four configured classes; Analytics says verified performance metrics are unavailable; registered model metrics are labeled unverified | PASS | Browser checks confirmed prior homepage and Analytics percentage figures are absent |
| Patient registration and dashboard | Registered a synthetic test user through the browser form | Registration returns a JWT and navigates to the patient dashboard | Navigated to `/dashboard`; welcome heading and dashboard sections rendered | PASS | Browser URL and heading snapshot |
| Successful and invalid login | Browser login with seeded local demo account, then an incorrect account/password | Valid login opens dashboard; invalid login shows an error | Valid login opened the dashboard; invalid credentials returned HTTP 401 and displayed `Invalid email or password` | PASS | Browser route, authenticated `/api/auth/me` HTTP 200, inline login error |
| JWT persistence across backend restart | Restarted backend twice with the same isolated DB and development key; reused browser token | Existing token remains valid after restart | `/api/auth/me` returned HTTP 200 with patient role after restart; browser remained on protected route | PASS | Post-restart browser request and page reload |
| Role authorization | Live API calls as patient and doctor | Restricted endpoints deny the wrong role | Patient-to-doctor-profile and doctor-to-patient-progress requests returned HTTP 403; unrelated doctor could not read patient analysis | PASS | Live API status assertions |
| Doctor profile/search and availability | Saved doctor profile; searched by city/specialization; created and listed two future slots | Profile is searchable and slots are returned available | Profile appeared in search; both slots returned available | PASS | Live API responses |
| Appointment booking and conflict | Booked a slot, then attempted the same slot again | First request persists; duplicate is rejected | First booking returned HTTP 200; duplicate returned HTTP 409; patient and doctor appointment lists returned HTTP 200 | PASS | Live API status assertions |
| Appointment approval, notes, notifications, progress | Doctor approved appointment, added note; patient fetched progress/notifications and marked notification read | Updates and notes persist and are visible to the patient | Approval, note, notification, read-state update, and progress requests returned HTTP 200; note appeared in progress | PASS | Live API assertions |
| Analysis record persistence | Saved a record through the UI and API; retrieved it through `/api/analysis/records` and checked SQLite | Saved record is retrievable and persisted | Browser/API retrieved the saved synthetic record; isolated SQLite query found it before test cleanup | PASS | API response and SQLite count assertion |
| MRI file selection and upload | Selected a generated non-patient PNG in the browser and submitted it | Upload reaches prediction endpoint and returns a result | Browser displayed the model result and four class probabilities; result was saved to the test account | PASS | Browser analysis page and record retrieval |
| Invalid MRI upload | Submitted unsupported MIME type and a corrupt PNG | Invalid inputs are rejected with an error | API returned `INVALID_IMAGE`; the corrupt-image response was HTTP 200 with an application-level error code | PASS | Live `/api/predict` responses |
| Invalid-image error display | Submitted corrupt PNG through the UI before and after the fix | Backend validation error is visible to the user | Initially the UI silently hid `error_code`; after fix it displays the backend validation message | PASS (after fix) | Browser before/after interaction; visible `Invalid image: Validation error...` |
| Real ResNet50 inference | Sent a generated synthetic image to `/api/predict` using the registered checkpoint | Loaded model returns a configured class and valid probabilities | Checkpoint loaded and inference completed; returned one of the four configured classes; probabilities were finite, in `[0,1]`, and summed to 1 | PASS (synthetic input only) | HTTP 200, no `error_code`; class/probability assertions; synthetic data is not an MRI result |
| Grad-CAM generation and serving | Sent synthetic image to `/api/explain`; fetched both returned asset URLs | Heatmap and overlay are generated and match source dimensions | Both PNGs were served; heatmap and overlay dimensions were 224x224 | PASS (synthetic input only) | HTTP 200; image decode and dimension assertions |
| Grad-CAM browser display | Uploaded synthetic image on `/explainability` and generated explanation | Prediction, heatmap, and overlay render | Prediction displayed; both images loaded in the browser at 224x224 | PASS (synthetic input only) | Browser DOM image dimensions and HTTP 200 asset fetch |
| Class mapping | Compared registry, inference outputs, and response keys | Four configured class labels agree | `NonDemented`, `VeryMildDemented`, `MildDemented`, and `ModerateDemented` matched | PASS | `models/registry.json`, `/api/models/`, prediction assertions |
| CLAHE preprocessing | Inspected the active inference preprocessing code | CLAHE should execute if included in the live inference path | Active prediction preprocessing performs RGB conversion, resizing, and ImageNet normalization; CLAHE is not in that path | NOT TESTED | `backend/app/ml/inference/inference_service.py`; no CLAHE call in the active path |
| U-Net segmentation | Checked registry, available model files, and inference route | U-Net loads and returns a segmentation output if available | The registry lists only ResNet50 and `backend/models` contains only the ResNet50 checkpoint; no active U-Net segmentation stage was executed | BLOCKED | `models/registry.json`; `backend/models/resnet50_best.pth` |
| Real MRI dataset coverage | Ran `scripts/validate_mri_dataset.py` | Real samples are present in all four categories | Validator found 0 images in each category and exited with code 2 | BLOCKED | Validator output lists 0 images for all four classes |
| Patient reports/download | No end-to-end report-download workflow was run | A report is generated and downloadable | Not verified in this run | NOT TESTED | Requires a separate report-generation test |
| Frontend production build and type-check | `npm.cmd run build` in `frontend` | TypeScript build and Vite production bundle complete | Exit code 0; Vite built 1,592 modules | PASS | Build output |
| Frontend lint | `npm.cmd run lint` in `frontend` | ESLint runs | Exit code 1: `'eslint' is not recognized as an internal or external command` | BLOCKED | ESLint executable is absent from the installed frontend dependencies |
| Backend regression suite | `python -m pytest -q` with `ALZHEIMERS_DB_PATH` set to a fresh temp DB | All existing tests pass | 7 passed; 28 deprecation warnings | PASS | Pytest output; warnings concern Pydantic class-based config and `datetime.utcnow()` |
| Python dependency consistency | `.venv\Scripts\python.exe -m pip check` | No broken requirements | No broken requirements found | PASS | pip output |

## Model and clinical-data boundaries

The live prediction and Grad-CAM checks used only a generated synthetic image. They prove that the installed checkpoint and local request path executed; they do **not** demonstrate performance on MRI data, model accuracy, clinical validity, or diagnostic utility. No real MRI image samples were found in the configured dataset folders.

The repository contains U-Net architecture code, but the live registry and available checkpoint do not provide a trained U-Net model. The active prediction route runs ResNet50 directly; a CLAHE-to-U-Net segmentation pipeline is not present in the tested inference path. Segmentation shape/type and real-data performance therefore remain unverified.

Browser testing emitted React Router v6 future-flag warnings. The 401 response logged during the invalid-login check was expected; no other uncaught browser error was observed during the successful workflows.

## Defects found and changes made

- [frontend/src/pages/app/AnalysisPage.tsx](../frontend/src/pages/app/AnalysisPage.tsx): prediction responses containing an application-level `error_code` were previously stored but not rendered. The page now shows the returned error message and does not save an errored result.
- [frontend/src/pages/public/HomePage.tsx](../frontend/src/pages/public/HomePage.tsx), [frontend/src/pages/app/AnalyticsPage.tsx](../frontend/src/pages/app/AnalyticsPage.tsx), and [frontend/src/pages/app/ModelsPage.tsx](../frontend/src/pages/app/ModelsPage.tsx): removed unsupported accuracy percentages from the public/Analytics claims, replaced the home statistic with the verified four configured classes, and labeled registry metrics as unverified metadata.
- [run_backend.py](../run_backend.py): the project launcher used port 8000 while the pre-existing Vite proxy targeted 8001. The launcher now uses 8001; the exact launcher and proxy were verified together.
- [backend/app/core/database.py](../backend/app/core/database.py): added `ALZHEIMERS_DB_PATH` to support isolated local test/live databases without resetting or replacing `data/app.db`.
- [backend/app/api/routes/analysis.py](../backend/app/api/routes/analysis.py): analysis records now use the same database connection helper as the rest of the backend, so the isolated path applies consistently.
- [README.md](../README.md): aligned the local backend command and URLs with the verified port; documented the stable development-only JWT fallback.
- The prior changes remain present: [requirements.txt](../requirements.txt) uses `httpx` instead of the invalid `httpx2` package, and [backend/app/core/auth.py](../backend/app/core/auth.py) uses a stable development fallback while retaining the `SECRET_KEY` environment override.
- Existing user-edited frontend configuration was retained: the Vite proxy still targets 8001 and the package dev script still binds Vite to `127.0.0.1`.

## Data-safety note

The live server, live API workflow, and final backend test run used isolated temporary SQLite databases. The synthetic API users and their dependent test rows were cleaned from the isolated live database; the application-seeded demo account remains there for local use. Generated Grad-CAM outputs from the live synthetic checks remain in `backend/results/gradcam`; pre-existing result files were not changed.

An initial post-edit regression invocation ran before the temporary database override was set and therefore used the default database path. The test fixture cleans its unique test accounts, while application startup ensures a demo user exists if one is absent. No records were deleted from `data/app.db`; its exact pre-test row state was not captured, so whether startup inserted a demo row cannot be determined from this run.

## Remaining verification steps

1. Obtain authorized, consent-cleared MRI samples for the four configured classes and run the dataset validator before attempting clinical or benchmark claims.
2. Supply and register an actual trained U-Net checkpoint if segmentation is a required workflow; then verify segmentation output shape/type and integration with classification.
3. Add/configure the frontend ESLint dependency and configuration if linting is required; lint could not run because the executable is missing.
4. Run a dedicated report-generation/download test. Real patient data must not be used in local demonstrations without authorization.

For an ordinary local run, from the project root use one terminal for `python run_backend.py` and another for `Set-Location frontend; npm.cmd run dev`. The backend listens at `http://127.0.0.1:8001`, the frontend at `http://127.0.0.1:5173`, and the API docs at `http://127.0.0.1:8001/docs`. To isolate local data as in this run, set `ALZHEIMERS_DB_PATH` to a temporary SQLite path before starting the backend.

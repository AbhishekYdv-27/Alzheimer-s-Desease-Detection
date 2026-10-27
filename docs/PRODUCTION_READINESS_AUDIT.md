# Production Readiness Audit

**Audit date:** 2026-10-24
**Scope:** Repository configuration and code review, isolated local backend/frontend execution, automated checks, and local browser/API smoke tests. No Vercel or Render deployment was performed.

## Executive verdict

**NO-GO for public production deployment.** The local checkpoint loads strictly and was exercised on synthetic input, but its training provenance and diagnostic performance are unverified. NPM advisories were resolved, public doctor self-assignment was disabled, and private checkpoint provisioning was implemented. Hosted checkpoint credentials, a verified expected digest, persistent storage, authorized labeled MRI data, production origins, and operational controls remain unavailable or unverified.

## Verified local results

| Area | Evidence | Status |
|---|---|---|
| Backend startup | FastAPI served on `http://127.0.0.1:8001`; `/health` returned HTTP 200. | PASS locally |
| Frontend startup | Vite served on `http://127.0.0.1:5173`; production build completed before the latest UI adjustments. A final build is recorded in [PRODUCTION_TEST_REPORT.md](./PRODUCTION_TEST_REPORT.md). | PASS locally |
| Browser workflow | Registration, dashboard loading, synthetic image upload/prediction, and Grad-CAM display were exercised in the local browser. | PASS for the listed synthetic workflow |
| API integration | Frontend service paths were compared with registered FastAPI routes; local browser traffic exercised the proxy and selected API operations. | Static mapping complete; runtime coverage partial |
| Inference | Local checkpoint loaded strictly; a live authenticated synthetic-image request returned four configured outputs and finite softmax values summing to 1. | PASS as software smoke test only; checkpoint provenance and clinical performance unverified |
| Grad-CAM | Protected heatmap and overlay were generated and displayed locally at the source image dimensions. | PASS locally; not clinical evidence |
| Persistence | An isolated SQLite database retained the test account and analysis through a controlled backend lifecycle restart. | PASS in isolated local test |
| Dataset | Dataset validator found no samples in any of the four configured class directories. | BLOCKED for real-data evaluation |
| Hosted deployment | No Vercel/Render credentials or production URLs were supplied; no deployment was attempted. | NOT TESTED |

See [PRODUCTION_TEST_REPORT.md](./PRODUCTION_TEST_REPORT.md) for commands, output, and workflow-level evidence.

## Changes made during this audit

- Enforced production JWT secret requirements and rejected placeholder secrets.
- Required an absolute SQLite database path in production; enabled SQLite foreign keys and disabled demo-account creation in production.
- Restricted production CORS to explicit HTTPS origins, methods, and headers.
- Required authentication for prediction/explanation operations and protected Grad-CAM assets by owner.
- Validated uploaded image bytes, decodability, dimensions, and size; used safe temporary filenames.
- Resolved model checkpoint paths portably, reported runtime checkpoint availability, and stopped exposing local filesystem paths in model responses.
- Routed frontend API and protected-image requests through the configured API base URL; required an absolute HTTPS backend URL for production builds.
- Removed an inaccurate claim that the dataset was connected and corrected public model/workflow claims to distinguish configured code from verified runtime capability.
- Removed duplicate root/health route definitions and added a regression test for unique OpenAPI operation IDs.
- Wired launcher and upload settings through the shared settings object, made relative local database paths project-root-relative, and pinned the current tested Python version.
- Added ESLint configuration/dependencies and regression coverage for safety-related fixes.
- Resolved all npm audit advisories with reviewed Vite, React Router, and Tailwind upgrades.
- Restricted public registration to patient accounts and added a staff-operated, audit-logged doctor provisioning CLI.
- Added private HTTPS checkpoint provisioning with bearer authentication, checksum validation, size limits, redirect rejection, atomic replacement, and safe unavailable behavior.
- Removed unsupported accuracy/experiment claims from both registry copies and mark checkpoint training provenance `UNVERIFIED`; strict local loading does not establish origin or clinical validity.

## Production blockers

1. **Checkpoint delivery:** `backend/models/resnet50_best.pth` exists locally and was used for the synthetic smoke test, but Git ignores `backend/models/*.pth`. Private artifact provisioning is implemented but has not been exercised against trusted remote storage. Supply the artifact, owner-verified SHA-256, private URL/token, and absolute `MODEL_CHECKPOINT_PATH`.
2. **Persistent storage:** The Render blueprint does not attach a disk or select a paid plan. Set `ALZHEIMERS_DB_PATH` to a file on a provisioned persistent disk. Generated Grad-CAM files also need a retention/cleanup policy and persistent or ephemeral-storage decision.
3. **No evaluation data:** The repository has no authorized labeled MRI dataset. The latest validator found zero images in all four expected class directories. Real-MRI evaluation, class coverage, calibration, and clinical performance are unverified; no accuracy claim is justified.
4. **Doctor credential review:** Public registration rejects doctor-role assignment. Staff provisioning requires a human review confirmation and records the operator/method, but credential verification remains the operator's responsibility.
5. **Operational controls:** Rate limiting, account verification/password reset, token revocation, image-retention controls, monitoring/alerting, and a tested backup/restore procedure are not verified.
6. **Hosted integration:** Actual Vercel/Render CORS, environment configuration, persistent storage, model artifact download, memory limits, and browser-to-hosted-API behavior have not been tested.

Detailed security findings are in [PRODUCTION_SECURITY_CHECKLIST.md](./PRODUCTION_SECURITY_CHECKLIST.md). Deployment prerequisites and owner actions are in [DEPLOYMENT_BLOCKERS.md](./DEPLOYMENT_BLOCKERS.md).

## Launch commands

From the repository root, create `.env` from `.env.example`, configure a strong local `SECRET_KEY`, and run:

```powershell
.\.venv\Scripts\python.exe run_backend.py
```

In a second PowerShell terminal:

```powershell
Set-Location frontend
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

The local Vite proxy targets the backend at `http://127.0.0.1:8001`; the production frontend must instead use the absolute HTTPS Render API URL ending in `/api`.

## Required decision before deployment

Do not deploy publicly until an owner-verified checkpoint digest/artifact source is configured, persistent storage and production API/CORS URLs are available, authorized model evaluation is performed, and operational controls are reviewed. NPM audit is clean and doctor self-assignment is blocked, but these changes do not establish hosted readiness or clinical validity. No deployment, commit, or external upload was performed.

# Vercel + Render Deployment Runbook

**Audit date:** 2026-10-27
**Status:** Preparation complete; codebase verified. Lint clean, build passes, backend 38 tests pass. No production deployment performed. Codebase-level checks resolved; data and model provenance remain blocked.

Review [DEPLOYMENT_BLOCKERS.md](./DEPLOYMENT_BLOCKERS.md). Before launch, provision the checkpoint and persistent storage, configure production origins and secrets, and complete authorized model evaluation. Dependency audit is currently clean, and public doctor self-assignment is disabled. Do not upload patient data to test the deployment.

## Preflight: do not deploy until all blockers are cleared

Review [DEPLOYMENT_BLOCKERS.md](./DEPLOYMENT_BLOCKERS.md). Before launch, provision the checkpoint and persistent storage, configure production origins and secrets, and complete authorized model evaluation. Dependency audit is currently clean, and public doctor self-assignment is disabled. Do not upload patient data to test the deployment.

## Render backend

1. Create or select a private Render service connected to the reviewed repository/branch. Do not deploy unreviewed local modifications.
2. Use the repository `render.yaml` blueprint:
   - Build command: `pip install -r requirements.txt`
   - Start command: `python run_backend.py`
   - Health check: `/health`
3. Select a service plan that supports the required persistent disk and has enough memory for the PyTorch runtime and configured checkpoint. The current blueprint does not select a plan or attach a disk.
4. Attach a persistent disk mounted at `/var/data` (or use a different mount and update both paths). Set:
   - `ALZHEIMERS_DB_PATH=/var/data/alzheimers.sqlite3`
   - `MODEL_CHECKPOINT_PATH=/var/data/resnet50_best.pth`
5. Provision the checkpoint from a trusted private source. The repository ignores `backend/models/*.pth`. Either place the artifact on the mounted disk or configure `MODEL_ARTIFACT_URL`, `MODEL_ARTIFACT_TOKEN`, and the owner-verified `MODEL_CHECKPOINT_SHA256`. Provisioning requires HTTPS, verifies the checksum, rejects redirects, caps size, and writes atomically. No artifact credentials or verified hosted artifact are currently available.
6. Configure `CORS_ORIGINS` with the exact Vercel production origin. Add preview origins only if they are intentionally approved.
7. Review `SECRET_KEY` and all variables in [DEPLOYMENT_ENVIRONMENT_VARIABLES.md](./DEPLOYMENT_ENVIRONMENT_VARIABLES.md). Keep `DEBUG=false`; do not set a public demo account.
8. After deployment, verify `/health`, `/api/health/`, `/api/models/status`, login/registration policy, and authenticated ownership restrictions. Confirm a restart preserves the database and model availability.

## Vercel frontend

1. Import the repository into Vercel and set the project root to `frontend`.
2. Use the existing Vite build (`npm run build`) and `dist` output.
3. Set `VITE_API_URL` to the absolute HTTPS Render API root, for example `https://<service>.onrender.com/api`.
4. Redeploy after changing this build-time variable. Vite embeds it in the frontend bundle.
5. Confirm client-side routes load directly and the browser network panel shows requests to the Render API, with no CORS or mixed-content failures.
6. Add the exact production and approved preview origins to Render's `CORS_ORIGINS`, redeploy, and test a preflight request.

## Post-deploy smoke checks

- Anonymous `/health` and `/api/health/` return success without exposing sensitive settings.
- Production API rejects missing/invalid signing secrets and refuses to start with an insecure CORS origin or missing absolute database path.
- Public registration creates patient accounts only. Provision a doctor only after staff independently verifies credentials using `scripts/provision_doctor.py`.
- Authenticated prediction rejects missing credentials and malformed/oversized images.
- A provisioned model returns `available=true`; a missing model is reported unavailable rather than substituted with random weights.
- Model state system is consistent across all endpoints (`/api/models/`, `/api/models/status`, `/api/predict`, `/api/explain`, `/api/analysis`): all route through `check_model_ready()` → `check_model_availability()` → `validate_model_file()`. States: NOT_CONFIGURED, NOT_TRAINED, UNVERIFIED, TRAINING, TRAINED, FAILED, MODEL_NOT_AVAILABLE.
- Checkpoint loads with `weights_only=True`; class_names in checkpoint match registry (4 classes: NonDemented, VeryMildDemented, MildDemented, ModerateDemented).
- Owner can retrieve own Grad-CAM assets; another user and anonymous requester cannot. Grad-CAM generates dynamically per input (forward pass + gradient computation at target layer).
- Create a non-sensitive test record, verify retrieval, restart/redeploy, verify persistence, then remove only the isolated test record using the supported application flow.
- Confirm application logs do not contain secrets, bearer tokens, or image bytes. Review disk growth and establish retention/backup policy.
- Do not interpret a synthetic smoke test as clinical validation. The local checkpoint registry status is UNVERIFIED (not TRAINED); no SHA-256 configured; no real-MRI evaluation performed.

## Rollback and recovery

- Keep a known-good deployment revision and record the environment-variable values without copying secret values into tickets or Git.
- For an application rollback, redeploy the known-good revision and verify health/authentication. Do not delete or recreate the disk.
- Before any schema change, make a tested backup and confirm a compatible rollback path; the current project has no formal migration framework.
- If disk data is unavailable, stop writes and follow the approved backup recovery process. Do not initialize a replacement database over an existing disk.

## Local reproduction commands

From the repository root:

```powershell
.\.venv\Scripts\python.exe run_backend.py
```

In a second terminal:

```powershell
Set-Location frontend
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

Local development uses the Vite proxy and backend on port `8001`; production Vercel must use `VITE_API_URL` for the Render service.

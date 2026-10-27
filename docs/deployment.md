# Deployment Guide

## Production boundary

This is a research and education platform, not a certified medical device. Do not use predictions or Grad-CAM visualizations as a diagnosis. The repository has no authorized labeled MRI samples, and no clinical performance has been established.

## Vercel + Render

The intended deployment pairing is Vercel for the Vite frontend and Render for the FastAPI backend. Follow the detailed [Vercel + Render runbook](./DEPLOYMENT_RUNBOOK_VERCEL_RENDER.md), configure values from [DEPLOYMENT_ENVIRONMENT_VARIABLES.md](./DEPLOYMENT_ENVIRONMENT_VARIABLES.md), and resolve the items in [DEPLOYMENT_BLOCKERS.md](./DEPLOYMENT_BLOCKERS.md) before a public launch.

The backend blueprint is `render.yaml`; its health check uses `/health`. The frontend's `frontend/vercel.json` preserves client-side routes. Vercel production builds require `VITE_API_URL` to be an absolute HTTPS URL ending in `/api`. Render's `CORS_ORIGINS` must contain the exact frontend origin.

## Backend configuration and storage

Production requires:

- `APP_ENV=production`
- A unique `SECRET_KEY` of at least 32 unpredictable characters
- Explicit HTTPS `CORS_ORIGINS`
- An absolute `ALZHEIMERS_DB_PATH` on persistent storage
- A provisioned checkpoint path in `MODEL_CHECKPOINT_PATH` if model inference is required
- `DEBUG=false`

The active adapter is SQLite. `DATABASE_URL` is not used to select PostgreSQL; a PostgreSQL adapter and migrations do not currently exist. Render's blueprint intentionally leaves the disk path and checkpoint path for dashboard configuration; it does not attach a disk or implement checkpoint downloading. The local checkpoint is ignored by Git, so it is not included in a normal deployment.

The local backend command is:

```powershell
.\.venv\Scripts\python.exe run_backend.py
```

`run_backend.py` reads `HOST` and `PORT` through the shared settings, allowing local defaults (`127.0.0.1:8001`) and the hosting provider's bind values.

## Frontend build

```powershell
Set-Location frontend
npm.cmd ci
npm.cmd run build
npm.cmd run lint
```

The production API base is a build-time Vite variable. Do not place secrets in `VITE_*` values. For local development, Vite proxies `/api` to `http://127.0.0.1:8001`.

## Operations and data safety

Before accepting sensitive images, define access, consent, retention/deletion, backup, and recovery policies. Configure HTTPS, secrets management, log retention/redaction, request-size limits, monitoring, and alerting. No production backup/restore drill or hosted resource-capacity test has been performed.

## Dataset validation

Run `py -3 scripts/validate_mri_dataset.py` before evaluating the model. The command exits non-zero if any of the four class directories lacks real image samples. Never use synthetic or unrelated images as clinical validation evidence. A successful local synthetic inference smoke test is not model evaluation.

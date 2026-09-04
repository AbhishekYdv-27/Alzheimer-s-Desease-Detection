# Deployment Guide

## Production boundary

This application is a research and education platform, not a certified medical device. Do not use predictions or Grad-CAM visualizations as a diagnosis.

## Environment

Copy `.env.example` to `.env` and set a unique secret:

```powershell
Copy-Item .env.example .env
```

Required production values:

- `SECRET_KEY`: long random value, never commit it.
- `CORS_ORIGINS`: comma-separated HTTPS frontend origins only.
- `HOST` and `PORT`: bind values supplied by the hosting provider.
- `DATABASE_URL`: use managed PostgreSQL with a compatible database adapter before multi-worker production use. The current SQLite adapter is for local and single-process deployments.
- `DEBUG`: keep `false` in production.

## Backend

Install dependencies, then run a process manager or hosting provider command equivalent to:

```powershell
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Expose `/health` and `/api/predict/health` as health checks. Use HTTPS termination, restricted network access to the database, log redaction, backups, and a managed secrets store.

The backend emits structured request, startup, shutdown, and unhandled-error logs through Python logging. Do not log request bodies, passwords, bearer tokens, uploaded images, or raw medical data. Configure the hosting provider to retain logs and alert on 5xx responses.

### Render

The repository includes `render.yaml`. Create the service from that blueprint, set `CORS_ORIGINS` to the deployed frontend origin, and configure persistent storage or a managed database for any data that must survive redeploys.

### Railway

Create a Python service from the repository with build command `pip install -r requirements.txt` and start command `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`. Set the same environment variables in Railway and attach a managed database only after the PostgreSQL adapter and migrations are implemented.

## Frontend

```powershell
Set-Location frontend
npm.cmd ci
npm.cmd run build
npm.cmd run preview -- --host 0.0.0.0
```

Configure the reverse proxy so `/api` routes to the backend and the frontend origin is included in `CORS_ORIGINS`.

For a separately hosted backend, set `VITE_API_URL=https://your-api.example.com/api` in the frontend build environment. The Vercel configuration in `frontend/vercel.json` preserves client-side routes. If frontend and backend share a reverse proxy, leave `VITE_API_URL=/api`.

## Database

`init_db()` creates missing local tables and adds compatible columns for the SQLite development database. Production deployments need versioned migrations, backups, and a PostgreSQL adapter before switching away from the local SQLite file.

## MRI validation

Run `py -3 scripts/validate_mri_dataset.py` before evaluating the model. The command exits non-zero if any of the four class directories lacks real image samples. Never use synthetic or unrelated images as clinical validation evidence.

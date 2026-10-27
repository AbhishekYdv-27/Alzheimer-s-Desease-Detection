# Deployment Environment Variables

**Audit date:** 2026-10-27
Verified: npm audit clean; backend tests 38 passed; frontend lint 0 errors, 0 warnings; model registry consistently reports UNVERIFIED status (no SHA-256 configured); checkpoint integrity validation exists (`checkpoint_sha256_matches`) but not active in the local artifact. Set values in the Render service and Vercel project dashboards. Do not commit production secrets or patient data.

## Render backend

| Variable | Required value | Secret? | Notes |
|---|---|---:|---|
| `APP_ENV` | `production` | No | Enables production safety checks. |
| `SECRET_KEY` | At least 32 unpredictable characters | **Yes** | Generate a unique secret in Render; do not copy the development fallback. |
| `HOST` | `0.0.0.0` | No | Required for Render's public service listener. |
| `PORT` | Render-provided | No | Read by shared settings; do not hard-code a production port. |
| `CORS_ORIGINS` | Exact HTTPS Vercel origin(s), e.g. `https://your-app.vercel.app` | No | Comma-separated explicit origins; no wildcard and no trailing `/api`. Add custom domain only when configured. |
| `ALZHEIMERS_DB_PATH` | Absolute persistent-disk file path, e.g. `/var/data/alzheimers.sqlite3` | No | Requires a mounted persistent disk at `/var/data`; current Render blueprint does not provision one. |
| `MODEL_CHECKPOINT_PATH` | Absolute checkpoint path, e.g. `/var/data/resnet50_best.pth` | No | Put the checkpoint on the mounted disk or use the private artifact provisioning settings below. |
| `MODEL_CHECKPOINT_SHA256` | 64-character SHA-256 of the owner-verified artifact | No | Required in production. Provisioning and readiness fail closed if this is missing or invalid. |
| `MODEL_ARTIFACT_URL` | HTTPS URL for a private checkpoint artifact | No | Optional only when the checkpoint is already present and matches the configured digest. Redirects are rejected. |
| `MODEL_ARTIFACT_TOKEN` | Private artifact bearer token | **Yes** | Required with `MODEL_ARTIFACT_URL`; keep it in Render secrets, never in Git or a `VITE_*` variable. |
| `JWT_ALGORITHM` | `HS256` | No | Keep consistent with the deployed token implementation. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` or a shorter approved duration | No | Tokens are not revocable server-side before expiry. |
| `DEBUG` | `false` | No | Keep disabled in production. |
| `MAX_UPLOAD_SIZE_BYTES` | `10485760` | No | 10 MiB application-level upload limit; also configure proxy limits. |
| `MAX_IMAGE_PIXELS` | `20000000` | No | 20 million decoded-pixel limit. Review against approved image dimensions. |

Render supplies `PORT` automatically. `render.yaml` supplies `APP_ENV`, `HOST`, the generated secret, JWT settings, and prompts for CORS/database/checkpoint/artifact values. A persistent disk still requires a plan and dashboard configuration; the blueprint does not provision one.

## Vercel frontend

| Variable | Required value | Secret? | Notes |
|---|---|---:|---|
| `VITE_API_URL` | `https://<render-service>.onrender.com/api` | No | Must be the absolute HTTPS backend API root and end in `/api`. The production build fails explicitly if this is absent or invalid. |

Vite variables are embedded into the client bundle. Never place credentials, private signing keys, or database connection secrets in `VITE_*` variables.

## Local development

Copy `.env.example` to `.env`. The example uses development settings and a project-relative SQLite path; relative database paths resolve from the repository root. Use a non-production local secret. The default local Vite proxy targets `http://127.0.0.1:8001`.

## Variables not to configure

`DATABASE_URL` is not consumed by the active SQLite adapter. Setting it does not switch the app to PostgreSQL. A managed SQL service requires a real adapter, migrations, and tests before it can be used.

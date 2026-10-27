# Deployment Blockers

**Audit date:** 2026-10-27
Codebase verified: frontend lint clean (0 errors, 0 warnings), frontend build passes, backend 38 tests pass, model checkpoint loads with `weights_only=True` and class_names match registry, model state system consistent across all API endpoints, Grad-CAM dynamic per input, preprocessing consistent (resize 224×224 + ImageNet normalize in both train and inference; CLAHE not present in active path). No production deployment attempted.

| Blocker | Current evidence | Owner action to unblock |
|---|---|---|
| No production environment/account access | No Vercel/Render URL, credentials, or deployment access were provided. | Create/configure private Vercel and Render projects; provide approved public origins for testing. |
| Checkpoint not in deployable tree | Local `backend/models/resnet50_best.pth` is Git-ignored and registry status is UNVERIFIED (not TRAINED). Checkpoint integrity validation exists (`checkpoint_sha256_matches` in `checkpoint_integrity.py`) but no SHA-256 is configured for the local artifact. Private HTTPS artifact provisioning with token authentication, size limit, redirect rejection, SHA-256 validation, and atomic replacement is implemented but has not been run against real storage. | Owner-verify the artifact, provide its 64-character digest and private HTTPS URL/token in Render, set the absolute checkpoint path, and test remote provisioning. |
| No persistent disk | Render blueprint has no mounted disk and `ALZHEIMERS_DB_PATH` is a dashboard-supplied value. | Select a plan supporting persistent disks, mount one, configure absolute DB/model paths, and test restart persistence/restore. |
| No real labeled dataset | Latest validator run reported zero images in each expected class directory and exited 2. | Supply authorized, consented and appropriately labeled data; define holdout evaluation and provenance. |
| Model provenance/validity unestablished | The local checkpoint loads strictly and ran on synthetic input, but its origin/training history are unverified. Registry reports UNVERIFIED status (not TRAINED); no SHA-256 configured; accuracy claims not independently verified. Unsupported registry accuracy and experiment claims were removed. No real-MRI performance, calibration, or clinical evaluation is available. | Verify checkpoint provenance, then run a documented independent evaluation with an authorized holdout dataset. Do not make clinical or diagnostic claims before appropriate validation. |
| Doctor credential review | Public self-assignment is rejected. Staff-only CLI provisioning records the operator and review method, but does not verify credentials independently. | Require an authorized operator to perform and document professional credential review before provisioning. |
| NPM advisories | Latest `npm audit` reports zero vulnerabilities after reviewed updates to Vite, React Router, and Tailwind. Codebase lint clean (0 errors, 0 warnings). | No unresolved npm advisory action remains; repeat audit as part of future dependency updates. |
| No account lifecycle / abuse controls verified | No password reset, account verification, login throttling, or token revocation was verified. | Decide and implement controls suitable for public deployment. |
| Image and generated-asset retention unclear | Grad-CAM assets are written locally; no cleanup schedule or patient-data retention policy was verified. | Define consent, storage, deletion, retention, and backup policy; implement scheduled cleanup where required. |
| Hosted resource fit unknown | PyTorch model memory/startup and upload resource limits were not tested on Render. | Choose a suitable plan, provision the checkpoint, and test startup, memory, latency, and request limits. |
| Operations not verified | No production monitoring, alerting, backup/restore drill, or incident procedure was exercised. | Configure and test operational runbooks before launch. |

## Deployment go/no-go

**NO-GO** until at least the checkpoint, persistent storage, doctor-account provisioning, dependency advisories, and production origin configuration have owners and verified resolution. Real-data/model validity remains a separate scientific and clinical governance requirement; local software execution does not resolve it.

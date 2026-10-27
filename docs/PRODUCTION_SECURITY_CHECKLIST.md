# Production Security Checklist

**Audit date:** 2026-10-24
**Scope:** Code/configuration review and local verification. This is not a third-party penetration test or a security certification.

## Controls verified in code

| Control | Result | Evidence / limitation |
|---|---|---|
| Production JWT secret | Implemented | Production startup rejects missing, placeholder, default, or too-short secrets. Local development retains a stable fallback; never use it in production. |
| Token signing | Implemented | JWT algorithm and expiration are settings-backed. No server-side revocation/denylist exists; tokens remain valid until expiry. |
| Password handling | Implemented | Passwords are hashed; never stored in plaintext. Password reset/verification and login throttling were not found. |
| Authentication on inference | Implemented | Prediction and explanation endpoints require bearer authentication. Regression tests cover unauthenticated rejection. |
| Image upload validation | Implemented | Upload size and decoded pixel-count bounds, image-byte format sniffing, full decode validation, canonical file suffix, and safe temporary-file handling. Defaults: 10 MiB and 20 million pixels. |
| Grad-CAM privacy | Implemented | Generated assets are served by an authenticated route, not a public static mount. The owner ID is associated with the generated filename and checked on retrieval. |
| Production CORS | Implemented | Requires explicit HTTPS origins and restricts methods/headers; cookie credentials are disabled. Actual deployed origin has not been configured or tested. |
| SQLite foreign keys | Implemented | Foreign-key enforcement is enabled on database connections and tested. |
| Production database path | Implemented | Production requires an explicitly configured absolute `ALZHEIMERS_DB_PATH`. The path must be on persistent storage to survive host replacement. |
| Demo credentials | Implemented | Automatic demo account creation is disabled in production. |
| Public doctor-role escalation | Fixed | Registration forbids extra role fields and always creates patient accounts; profile updates cannot change the role. Regression tests cover both paths. |
| Doctor provisioning | Implemented with human trust boundary | `scripts/provision_doctor.py` requires operator confirmation, records the operator/review method, and creates a doctor profile. It does not independently validate credentials. |
| Model artifact provisioning | Implemented, not hosted-verified | Private HTTPS download uses a bearer token, rejects redirects, enforces a size cap and SHA-256 digest, writes atomically, and fails closed. Real artifact credentials/source were not supplied. |
| Model checkpoint integrity/loading | Implemented and locally smoke-tested | Production requires a configured SHA-256; loader uses `weights_only=True`, validates class labels and strict state-dict loading. Missing checkpoints do not fall back to random weights. |
| Model provenance/performance claims | Corrected | Registry status is `UNVERIFIED`; unsupported accuracy/experiment metadata was removed. A locally loadable checkpoint does not prove provenance or diagnostic performance. |
| NPM dependency audit | Resolved locally | Vite, React Router, and Tailwind were upgraded; latest `npm audit` returned zero vulnerabilities. |
| Filesystem path disclosure | Fixed | Model API responses no longer disclose local checkpoint paths. |
| API error details | Improved | Prediction failures are logged server-side and returned without raw internal exception details. |
| OpenAPI operation IDs | Verified | Regression test asserts operation IDs are unique. OpenAPI/docs remain enabled and publicly accessible unless deployment policy changes them. |

## Unresolved risks and required controls

| Severity | Finding | Required action before public launch |
|---|---|---|
| High | Browser bearer token is stored in local storage. A successful XSS could expose it; logout does not revoke it server-side. | Review CSP/XSS controls and choose an explicit token/session revocation strategy. |
| High | Checkpoint is ignored by Git; private artifact code has not been configured against trusted storage. | Provide an owner-verified artifact source, bearer secret, and expected SHA-256 through Render; test hosted provisioning. |
| High | Render persistent disk is not provisioned in the blueprint. SQLite and generated assets may be lost on redeploy/replacement. | Provision persistent storage, set the absolute path, and test restart/restore. |
| Medium | No verified rate limiting for login, registration, or inference; no account verification/password reset flow was found. | Add abuse controls and account lifecycle controls appropriate to public use. |
| Medium | No verified retention/cleanup schedule for uploaded images and generated Grad-CAM files. | Define consent, retention, deletion, backup, and access policies before accepting sensitive scans. |
| Medium | No verified production monitoring, alerting, dependency scanning automation, or tested backup/restore plan. | Configure these operational controls and exercise recovery before launch. |
| Medium | Public OpenAPI documentation is enabled. | Decide whether production docs should be public or disabled/protected. |
| Medium | SQLite is the only active adapter; multi-instance concurrency/scale and backup behavior have not been validated. | Use a single instance with tested persistent disk or implement/migrate to a managed database adapter. |
| Medium | Proxy/request-body limits and hosted memory/time limits have not been validated with the 10 MiB upload limit and PyTorch model. | Configure ingress limits and load-test within the expected deployment tier. |
| Blocking | No authorized labeled MRI test dataset exists in the repository; class metrics and calibration cannot be reproduced. Registry accuracy values were removed and none are claimed. | Obtain authorized data, document provenance/consent, and run a proper holdout evaluation. |
| Blocking | No deployed Vercel/Render origins or credentials were available. | Configure the frontend API URL and matching CORS allowlist, then run hosted smoke tests. |

## Safe handling notes

- Do not place real patient scans, credentials, JWT secrets, or model weights in Git or public artifacts.
- Do not use synthetic inputs or registry metadata as diagnostic-performance evidence.
- The classifier is a research prototype, not a clinically validated medical device.
- The local smoke test used a synthetic image and is not evidence of diagnostic accuracy.

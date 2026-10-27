# API Integration Matrix

**Audit date:** 2026-10-24
**Scope:** Frontend API service calls compared with FastAPI's registered routes and request/response declarations. A static route match is not a claim that every workflow was exercised end-to-end.

## Frontend service operations

| # | Frontend operation | HTTP request path | Backend route | Auth | Contract / evidence |
|---:|---|---|---|---|---|
| 1 | `authApi.login` | `POST /api/auth/login` | `POST /api/auth/login` | Public | Form credentials; returns bearer token/user. Browser registration/prediction tested; dedicated invalid-login UI flow not run in final pass. |
| 2 | `authApi.register` | `POST /api/auth/register` | `POST /api/auth/register` | Public | Creates patient accounts only; extra role fields are rejected. Local browser registration and API doctor-role rejection exercised. |
| 3 | `authApi.getMe` | `GET /api/auth/me` | `GET /api/auth/me` | Bearer | Current user. Used by authenticated app initialization. |
| 4 | `authApi.updateMe` | `PATCH /api/auth/me` | `PATCH /api/auth/me` | Bearer | Profile patch; returns user. Static path/contract match. |
| 5 | `authApi.updatePassword` | `PATCH /api/auth/password` | `PATCH /api/auth/password` | Bearer | Current/new password payload. Static path/contract match. |
| 6 | `modelsApi.getAll` | `GET /api/models/` | `GET /api/models/` | Bearer helper | Model metadata list. Trailing slash is explicit to avoid an unnecessary redirect. |
| 7 | `modelsApi.getByName` | `GET /api/models/{name}` | `GET /api/models/{model_name}` | Bearer helper | Model metadata by name. |
| 8 | `modelsApi.getStatus` | `GET /api/models/status` | `GET /api/models/status` | Bearer helper | Registry models plus actual checkpoint availability; consumed by dashboard/model/explainability surfaces. |
| 9 | `modelsApi.getReadiness` | `GET /api/models/{name}/readiness` | `GET /api/models/{model_name}/readiness` | Bearer helper | Per-model readiness response. |
| 10 | `modelsApi.compare` | `GET /api/models/compare/` | `GET /api/models/compare/` | Bearer helper | Model comparison response. |
| 11 | `analysisApi.getRecords` | `GET /api/analysis/records` | `GET /api/analysis/records` | Bearer | Current user's analysis list. Local persistence/retrieval exercised in the isolated smoke test. |
| 12 | `analysisApi.getRecord` | `GET /api/analysis/records/{id}` | `GET /api/analysis/records/{record_id}` | Bearer | One owned record. Static path/ownership contract match. |
| 13 | `analysisApi.getReport` | `GET /api/reports/analysis/{id}` | `GET /api/reports/analysis/{record_id}` | Bearer | Report response for an owned analysis. Local report retrieval exercised. |
| 14 | `analysisApi.createRecord` | `POST /api/analysis/records` | `POST /api/analysis/records` | Bearer | Prediction/report data; saved analysis. Local inference persistence exercised. |
| 15 | `analysisApi.getStats` | `GET /api/analysis/stats` | `GET /api/analysis/stats` | Bearer | Current user's summary statistics. Static path/contract match. |
| 16 | `analysisApi.predict` | `POST /api/predict` | `POST /api/predict` | Bearer | Multipart image and model name; local browser synthetic upload/inference exercised. |
| 17 | `analysisApi.explain` | `POST /api/explain` | `POST /api/explain` | Bearer | Multipart image/model; local Grad-CAM generation exercised. |
| 18 | `analysisApi.downloadReport` | `GET /api/analysis/records/{id}/download` | `GET /api/analysis/records/{record_id}/download` | Bearer | Download response; static path match. |
| 19 | `portalApi.getDoctors` | `GET /api/portal/doctors` | `GET /api/portal/doctors` | Public | Optional location/specialization query; static path/contract match. |
| 20 | `portalApi.getDoctorAvailability` | `GET /api/portal/doctors/{id}/availability` | `GET /api/portal/doctors/{doctor_id}/availability` | Public | Availability list; static path match. |
| 21 | `portalApi.setDoctorAvailability` | `POST /api/portal/doctors/availability` | `POST /api/portal/doctors/availability` | Bearer, doctor | Availability payload; static path/role match. |
| 22 | `portalApi.getMyDoctorProfile` | `GET /api/portal/doctor/profile` | `GET /api/portal/doctor/profile` | Bearer, doctor | Current doctor's profile. |
| 23 | `portalApi.updateDoctorProfile` | `PUT /api/portal/doctor/profile` | `PUT /api/portal/doctor/profile` | Bearer, doctor | Profile update payload. |
| 24 | `portalApi.bookAppointment` | `POST /api/portal/appointments` | `POST /api/portal/appointments` | Bearer, patient | Appointment request payload. |
| 25 | `portalApi.getMyAppointments` | `GET /api/portal/appointments` | `GET /api/portal/appointments` | Bearer | Current patient's appointments. |
| 26 | `portalApi.getDoctorAppointments` | `GET /api/portal/doctor/appointments` | `GET /api/portal/doctor/appointments` | Bearer, doctor | Doctor appointment list. |
| 27 | `portalApi.getDoctorPatients` | `GET /api/portal/doctor/patients` | `GET /api/portal/doctor/patients` | Bearer, doctor | Doctor patient list. |
| 28 | `portalApi.addDoctorNote` | `POST /api/portal/doctor/notes` | `POST /api/portal/doctor/notes` | Bearer, doctor | Appointment note payload. |
| 29 | `portalApi.updateAppointmentStatus` | `PATCH /api/portal/appointments/{id}/status` | `PATCH /api/portal/appointments/{appointment_id}/status` | Bearer, doctor | Status change payload; static path/role match. |
| 30 | `portalApi.getNotifications` | `GET /api/portal/notifications` | `GET /api/portal/notifications` | Bearer | Current user's notifications. |
| 31 | `portalApi.markNotificationRead` | `PATCH /api/portal/notifications/{id}/read` | `PATCH /api/portal/notifications/{notification_id}/read` | Bearer | Read state update. |
| 32 | `portalApi.getProgress` | `GET /api/portal/progress` | `GET /api/portal/progress` | Bearer | Current patient's progress summary. |
| 33 | `healthApi.check` | `GET /api/health/` | `GET /api/health/` | Public | Health response; local HTTP 200 was verified. |

The frontend wrappers map to registered backend routes. Runtime browser/API evidence is partial; the table does not imply registration of a doctor, appointment approval, availability changes, notes, or every report/download workflow was tested.

## Backend routes without a matching frontend wrapper

The backend also registers root/health information, model-specific status, prediction health, individual doctor details, and some lower-level record operations. They are not evidence of a frontend feature unless the UI calls them.

## Integration findings

- Frontend auth and model requests use the shared configured API base; production builds require an absolute HTTPS API URL ending in `/api`.
- Private Grad-CAM assets are fetched with the bearer token and displayed as authenticated Blob URLs.
- The model-list client path includes the backend's trailing slash to avoid FastAPI's 307 redirect.
- Vite local proxy and live local backend communication were exercised. Hosted Vercel-to-Render connectivity has not been tested.
- Role-specific portal operations are statically mapped. Public registration cannot assign the doctor role; staff-only CLI provisioning requires manual credential verification and records the operator/review method. This does not independently verify a doctor's credentials.

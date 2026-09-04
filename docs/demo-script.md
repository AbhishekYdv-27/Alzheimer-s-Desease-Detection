# Professional Demo Script

Target duration: 4-6 minutes

Audience: project reviewers, research collaborators, and technical stakeholders

## Before the demo

Start both services from the project root:

```powershell
py -3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
Set-Location frontend
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

Open http://127.0.0.1:5173 in a clean browser window. Keep two accounts ready:

- Patient: use the existing demo account shown on the login screen, or register a temporary patient account.
- Doctor: register a temporary doctor account in a second browser profile or after logging out.

For a reliable appointment demonstration, the doctor should publish at least two future slots from **Doctor Profile** before recording. For the AI section, use an authorized MRI sample only. The repository intentionally contains no MRI samples, so do not claim four-class clinical validation with unrelated images.

## Timeline at a glance

| Time | Segment | Route |
| --- | --- | --- |
| 0:00-0:25 | Landing and introduction | `/` |
| 0:25-0:45 | Registration and login | `/signup`, `/login` |
| 0:45-1:10 | Patient dashboard | `/dashboard` |
| 1:10-1:55 | ResNet50 prediction | `/analysis` |
| 1:55-2:25 | Grad-CAM explanation | `/explainability` |
| 2:25-3:05 | Find doctor and book | `/doctors` |
| 3:05-3:45 | Doctor workspace | `/doctor` |
| 3:45-4:20 | Approval and notifications | `/doctor/appointments`, `/appointments` |
| 4:20-4:40 | Logout and close | `/login` |

## 1. Landing page and introduction, 25 seconds

Open the landing page.

**Presenter narration:**

> This is an AI-assisted Alzheimer's research platform. It combines explainable MRI analysis with a secure care-team workflow. The system is designed for research and education, not confirmed diagnosis.

Point out the primary analysis action, the explainability language, and the research disclaimer. Open **Learn More** briefly if the audience needs the project context, then return to the landing page.

## 2. Registration and login, 20 seconds

Open **Start MRI Analysis** and show the account type selector on `/signup`.

- Select **Patient**.
- Mention that Doctor accounts unlock scheduling and patient-management tools.
- Use the prepared patient account and sign in.

**Presenter narration:**

> Authentication is role-aware. The same application presents different workflows for patients and doctors, while the backend enforces those roles on every protected API route.

Skip registration during a recorded demo if the account is already prepared.

## 3. Patient dashboard, 25 seconds

After login, show `/dashboard`.

Point out:

- Analysis record count.
- Model readiness.
- Appointment summary.
- Recent activity and research disclaimer.

**Presenter narration:**

> The dashboard is the patient’s overview: model readiness, analysis history, appointments, and care-team activity are visible without leaving the workspace.

Open the notification bell once to show the persistent notification panel if prior test data exists.

## 4. ResNet50 prediction, 45 seconds

Open **AI Analysis** at `/analysis`.

1. Confirm **ResNet50** is shown as ready.
2. Upload an authorized MRI image.
3. Click **Analyze Image**.
4. Show the predicted class, confidence, and class probability bars.

**Presenter narration:**

> The backend loads the registered ResNet50 checkpoint and returns a class prediction with probabilities and confidence. These values are presented as research output and are not a medical diagnosis.

If no authorized MRI sample is available, skip the upload and explain that the repository blocks unsupported validation rather than using synthetic evidence.

## 5. Grad-CAM explainability, 30 seconds

Open `/explainability`.

1. Upload the same authorized MRI image.
2. Click **Generate Explanation**.
3. Show the heatmap and MRI-plus-overlay views.
4. Point out the heatmap legend.

**Presenter narration:**

> Grad-CAM highlights the image regions that influenced the model output. It improves interpretability, but it does not identify a clinical finding or replace specialist review.

## 6. Find doctors and book an appointment, 40 seconds

Open `/doctors`.

1. Search by city or specialization if the doctor profile has those fields.
2. Select **View availability**.
3. Choose a future date.
4. Choose an open time slot.
5. Enter a short reason and request the appointment.

**Presenter narration:**

> Patients can only choose slots published by a doctor. Once a slot is requested, it disappears from the available list and duplicate booking is rejected by the backend.

Open `/appointments` briefly to show the pending request.

## 7. Doctor dashboard, 40 seconds

Log out from the patient account. Sign in with the prepared Doctor account.

Show `/doctor` and `/doctor/profile`.

Point out:

- Pending request count.
- Appointment count.
- Doctor profile.
- Availability publisher.

If the schedule was not prepared earlier, publish a future date with 30-minute intervals now. Then open `/doctor/appointments`.

**Presenter narration:**

> The Doctor portal is a separate role-aware workspace. Doctors control their public profile, publish bookable availability, and manage the incoming care workflow.

## 8. Approve or reject and show notifications, 35 seconds

On `/doctor/appointments`:

1. Open the notification bell and show the patient booking notification.
2. Approve one request or reject it.
3. Refresh the page to show the status persists.
4. Log back into the patient account.
5. Open the notification bell and show the approval or rejection notification.
6. Click the notification to mark it read.
7. Refresh once more to demonstrate the read state persists.

**Presenter narration:**

> Appointment decisions create durable notifications for the patient. Notifications are stored in the database, support unread/read state, and survive a browser refresh.

For a longer version, open the patient’s appointment history and show the final status beside the scheduled time.

## 9. Logout and close, 20 seconds

Use the sidebar **Logout** action.

**Presenter narration:**

> The session ends through the shared logout action. The platform closes with explicit research and safety boundaries: real MRI validation requires an authorized dataset, and model output must not be used as a diagnosis.

## Recovery notes

- **No doctors listed:** sign in as a doctor, complete the profile, save it, then return to the patient account.
- **No dates listed:** publish future availability from `/doctor/profile`; use a date after today.
- **Slot already unavailable:** choose the next visible slot. The conflict protection is working as intended.
- **Model not ready:** check `/api/predict/health` and the model registry before recording.
- **No MRI sample:** do not substitute a random image in a formal demo. Show the analysis interface and explain the dataset gate.
- **Notification count looks different:** existing local database history affects the count. Use temporary accounts or clear only test records in a disposable development database.

## Recording checklist

- Browser zoom at 100%.
- Desktop viewport for the main recording; capture one mobile notification panel as an optional appendix.
- Do not expose `.env`, tokens, patient data, or database files.
- Use only authorized MRI images.
- Keep the research disclaimer visible at the beginning and end.

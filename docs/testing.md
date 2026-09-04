# Testing Guide

## Automated tests

From the project root:

```powershell
pytest -q
```

The suite covers health, authentication and role ownership, availability slot creation, duplicate booking prevention, appointment approval and rejection, notification creation, and notification read persistence.

## MRI validation

The repository does not include patient MRI images. Check coverage with:

```powershell
py -3 scripts/validate_mri_dataset.py
```

The validator reports each of `NonDemented`, `VeryMildDemented`, `MildDemented`, and `ModerateDemented`, and refuses to claim coverage for missing classes. Once legitimate, consent-cleared samples are supplied, run prediction and Grad-CAM separately for every class and record model version, probabilities, confidence, and output paths.

## Frontend

```powershell
Set-Location frontend
npm.cmd run build
```

Manual browser checks should cover both roles, route redirects, appointment creation, unavailable slots, duplicate booking, approval/rejection, notification read state after refresh, mobile layout, and the ResNet50 prediction and Grad-CAM screens.

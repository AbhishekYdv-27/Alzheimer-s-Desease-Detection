from html import escape

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
import json

from backend.app.core.auth import get_current_user_id
from backend.app.api.routes.analysis import get_db

router = APIRouter(prefix="/api/reports", tags=["reports"])


def get_owned_record(record_id: str, user_id: str):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM analysis_records WHERE id = ? AND user_id = ?",
        (record_id, user_id),
    ).fetchone()
    conn.close()
    return row


@router.get("/analysis/{record_id}/download", response_class=HTMLResponse)
async def download_analysis_report(record_id: str, user_id: str = Depends(get_current_user_id)):
    row = get_owned_record(record_id, user_id)
    if not row:
        raise HTTPException(status_code=404, detail="Analysis record not found")

    fields = [
        ("Analysis ID", row["id"]),
        ("Image", row["image_name"]),
        ("Date", row["created_at"]),
        ("Model", row["model_name"]),
        ("Predicted class", row["predicted_class"] or "Not available"),
        ("Confidence", f"{row['confidence'] * 100:.2f}%" if row["confidence"] is not None else "Not available"),
        ("Status", row["status"]),
        ("Model version", row["model_version"]),
        ("Grad-CAM explanation", "Available" if row["explanation_available"] else "Not generated"),
    ]
    details = "".join(f"<dt>{escape(str(label))}</dt><dd>{escape(str(value))}</dd>" for label, value in fields)
    probabilities = json.loads(row["class_probabilities"]) if row["class_probabilities"] else {}
    probability_html = "".join(
        f"<dt>{escape(str(label))}</dt><dd>{float(value) * 100:.2f}%</dd>"
        for label, value in probabilities.items()
    )
    html = f"""<!doctype html><html><head><meta charset='utf-8'><title>Alzheimer Desease Detection Research Report</title>
<style>body{{font-family:Arial,sans-serif;max-width:760px;margin:40px auto;color:#20242a}}dt{{font-weight:bold;margin-top:14px}}dd{{margin:4px 0 0}}.note{{margin-top:32px;padding:14px;background:#fff4df;border:1px solid #e7b85c}}</style></head>
<body><h1>AI-Assisted Analysis Report</h1><p>Alzheimer Desease Detection research output</p><dl>{details}</dl>
<h2>Class probabilities</h2><dl>{probability_html or '<dd>Not stored for this analysis.</dd>'}</dl>
<p class='note'><strong>Research disclaimer:</strong> This report is an AI-assisted research or demonstration output. It is not a professional medical diagnosis and must not replace qualified clinical judgment.</p></body></html>"""
    return HTMLResponse(
        content=html,
        headers={"Content-Disposition": f'attachment; filename="analysis-report-{record_id}.html"'},
    )


@router.get("/analysis/{record_id}")
async def get_analysis_report(record_id: str, user_id: str = Depends(get_current_user_id)):
    row = get_owned_record(record_id, user_id)
    if not row:
        raise HTTPException(status_code=404, detail="Analysis record not found")
    return {
        "id": row["id"], "image_name": row["image_name"], "created_at": row["created_at"],
        "model_name": row["model_name"], "model_version": row["model_version"],
        "predicted_class": row["predicted_class"], "confidence": row["confidence"],
        "status": row["status"],
        "class_probabilities": json.loads(row["class_probabilities"]) if row["class_probabilities"] else None,
        "explanation_available": bool(row["explanation_available"]),
    }
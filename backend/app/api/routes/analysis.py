from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import json
from backend.app.core.auth import get_current_user
from backend.app.core.database import get_db

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


def can_access_patient(conn, current_user: dict, patient_id: str) -> bool:
    if current_user["id"] == patient_id:
        return True
    if current_user.get("role", "patient") != "doctor":
        return False
    return conn.execute("""SELECT 1 FROM appointments WHERE doctor_id = ? AND patient_id = ?
                          AND status IN ('pending', 'approved', 'completed') LIMIT 1""",
                        (current_user["id"], patient_id)).fetchone() is not None


class AnalysisRecordCreate(BaseModel):
    user_id: str
    image_name: str
    model_name: str
    predicted_class: str
    confidence: float
    status: str = "completed"
    model_version: str = "1.0"
    class_probabilities: Optional[dict[str, float]] = None
    explanation_available: bool = False


class AnalysisRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    image_name: str
    model_name: str
    predicted_class: str
    confidence: float
    status: str
    created_at: str
    model_version: str = "1.0"
    class_probabilities: Optional[dict[str, float]] = None
    explanation_available: bool = False

@router.post("/records", response_model=AnalysisRecord)
async def create_analysis_record(record: AnalysisRecordCreate, current_user: dict = Depends(get_current_user)):
    import uuid
    
    conn = get_db()
    cursor = conn.cursor()

    if not can_access_patient(conn, current_user, record.user_id):
        conn.close()
        raise HTTPException(status_code=403, detail="You are not authorized to save analysis for this patient")
    
    record_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    
    try:
        cursor.execute("""
            INSERT INTO analysis_records (id, user_id, image_name, model_name, predicted_class, confidence, status, created_at,
                model_version, class_probabilities, explanation_available)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (record_id, record.user_id, record.image_name, record.model_name, record.predicted_class,
               record.confidence, record.status, created_at, record.model_version,
               json.dumps(record.class_probabilities) if record.class_probabilities else None,
               int(record.explanation_available)))
        
        conn.commit()
        
        return AnalysisRecord(
            id=record_id,
            user_id=record.user_id,
            image_name=record.image_name,
            model_name=record.model_name,
            predicted_class=record.predicted_class,
            confidence=record.confidence,
            status=record.status,
            created_at=created_at,
            model_version=record.model_version,
            class_probabilities=record.class_probabilities,
            explanation_available=record.explanation_available,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/records", response_model=List[AnalysisRecord])
async def get_analysis_records(user_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    if not can_access_patient(conn, current_user, user_id):
        conn.close()
        raise HTTPException(status_code=403, detail="You are not authorized to view this patient's analyses")
    
    try:
        cursor.execute("""
            SELECT * FROM analysis_records 
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        
        rows = cursor.fetchall()
        
        records = [
            AnalysisRecord(
                id=row['id'],
                user_id=row['user_id'],
                image_name=row['image_name'],
                model_name=row['model_name'],
                predicted_class=row['predicted_class'],
                confidence=row['confidence'],
                status=row['status'],
                created_at=row['created_at'],
                model_version=row['model_version'],
                class_probabilities=json.loads(row['class_probabilities']) if row['class_probabilities'] else None,
                explanation_available=bool(row['explanation_available']),
            )
            for row in rows
        ]
        
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/records/{record_id}", response_model=AnalysisRecord)
async def get_analysis_record(record_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM analysis_records WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Record not found")
        if not can_access_patient(conn, current_user, row['user_id']):
            raise HTTPException(status_code=404, detail="Record not found")
        
        return AnalysisRecord(
            id=row['id'],
            user_id=row['user_id'],
            image_name=row['image_name'],
            model_name=row['model_name'],
            predicted_class=row['predicted_class'],
            confidence=row['confidence'],
            status=row['status'],
            created_at=row['created_at'],
            model_version=row['model_version'],
            class_probabilities=json.loads(row['class_probabilities']) if row['class_probabilities'] else None,
            explanation_available=bool(row['explanation_available']),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/stats")
async def get_analysis_stats(user_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    if not can_access_patient(conn, current_user, user_id):
        conn.close()
        raise HTTPException(status_code=403, detail="You are not authorized to view this patient's statistics")
    
    try:
        cursor.execute("SELECT COUNT(*) as total FROM analysis_records WHERE user_id = ?", (user_id,))
        total = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT predicted_class, COUNT(*) as count 
            FROM analysis_records 
            WHERE user_id = ? 
            GROUP BY predicted_class
        """, (user_id,))
        by_class = {row['predicted_class']: row['count'] for row in cursor.fetchall()}
        
        cursor.execute("""
            SELECT AVG(confidence) as avg_confidence 
            FROM analysis_records 
            WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        avg_confidence = row['avg_confidence'] if row['avg_confidence'] else 0
        
        return {
            "total_analyses": total,
            "by_class": by_class,
            "average_confidence": round(avg_confidence, 4) if avg_confidence else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def health_root():
    return {"status": "healthy", "service": "alzheimers-ai-platform"}
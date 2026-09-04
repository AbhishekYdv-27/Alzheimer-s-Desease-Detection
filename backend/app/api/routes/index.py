from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def root():
    return {
        "message": "Alzheimer's AI Platform API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@router.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "alzheimers-ai-platform"
    }

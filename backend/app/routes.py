from fastapi import APIRouter
from ..routes.admin import router as admin_router

router = APIRouter()

# Include admin routes
router.include_router(admin_router)

@router.get("/health")
def health_check():
    return {"status": "ok"}


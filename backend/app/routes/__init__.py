from fastapi import APIRouter
from ..routes import admin, auth, preferences

router = APIRouter()

# Include route modules
router.include_router(admin.router)
router.include_router(auth.router)
router.include_router(preferences.router)
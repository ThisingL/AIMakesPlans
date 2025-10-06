"""API v1 routes."""
from fastapi import APIRouter
from .tasks import router as tasks_router
from .parse import router as parse_router
from .schedule import router as schedule_router
from .user import router as user_router
from .preference_parse import router as preference_parse_router

router = APIRouter(prefix="/v1")

# Include sub-routers
router.include_router(tasks_router, tags=["tasks"])
router.include_router(parse_router, tags=["parse"])
router.include_router(schedule_router, tags=["schedule"])
router.include_router(user_router, tags=["user"])
# Merge preference parse router into user (they share the same prefix)
router.include_router(preference_parse_router, tags=["user"])


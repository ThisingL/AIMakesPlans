"""API v1 routes."""
from fastapi import APIRouter
from .tasks import router as tasks_router
from .parse import router as parse_router
from .schedule import router as schedule_router

router = APIRouter(prefix="/v1")

# Include sub-routers
router.include_router(tasks_router, tags=["tasks"])
router.include_router(parse_router, tags=["parse"])
router.include_router(schedule_router, tags=["schedule"])


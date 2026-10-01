from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin_router, devices_router, geofences_router, identity_router, locations_router
from app.core.config import get_settings
from app.db.session import Base, engine

settings = get_settings()

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(devices_router, prefix="/api/v1")
app.include_router(geofences_router, prefix="/api/v1")
app.include_router(identity_router, prefix="/api/v1")
app.include_router(locations_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")


@app.on_event("startup")
def create_tables_for_local_dev() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "geofencing-location-events", "mode": "event-detection"}


@app.get("/api/v1/status", tags=["system"])
def api_status() -> dict[str, str]:
    return {"api": settings.app_name, "status": "ready"}

from app.api.admin import router as admin_router
from app.api.devices import router as devices_router
from app.api.geofences import router as geofences_router
from app.api.identity import router as identity_router
from app.api.locations import router as locations_router

__all__ = ["admin_router", "devices_router", "geofences_router", "identity_router", "locations_router"]

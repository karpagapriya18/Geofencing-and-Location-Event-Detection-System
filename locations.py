from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import GeofenceEvent, LocationEvent
from app.schemas import DeviceLocationRead, GeofenceEventRead, LocationIngest, LocationIngestResponse
from app.services.detection import ingest_location

router = APIRouter(tags=["locations"])


@router.post("/locations", response_model=LocationIngestResponse, status_code=201)
def create_location(payload: LocationIngest, db: Session = Depends(get_db)):
    location, events = ingest_location(db, payload)
    return LocationIngestResponse(location_event_id=location.id, generated_events=events)


@router.post("/track-points", response_model=LocationIngestResponse, status_code=201)
def create_track_point(payload: LocationIngest, db: Session = Depends(get_db)):
    location, events = ingest_location(db, payload)
    return LocationIngestResponse(location_event_id=location.id, generated_events=events)


@router.get("/events", response_model=list[GeofenceEventRead])
def list_geofence_events(device_id: int | None = None, geofence_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(GeofenceEvent).order_by(GeofenceEvent.occurred_at.desc(), GeofenceEvent.id.desc())
    if device_id:
        query = query.filter(GeofenceEvent.device_id == device_id)
    if geofence_id:
        query = query.filter(GeofenceEvent.geofence_id == geofence_id)
    return query.limit(500).all()


@router.get("/boundary-events", response_model=list[GeofenceEventRead])
def list_boundary_events(device_id: int | None = None, geofence_id: int | None = None, db: Session = Depends(get_db)):
    return list_geofence_events(device_id=device_id, geofence_id=geofence_id, db=db)


@router.get("/geofences/{geofence_id}/activity", response_model=list[GeofenceEventRead])
def geofence_activity(geofence_id: int, db: Session = Depends(get_db)):
    return (
        db.query(GeofenceEvent)
        .filter(GeofenceEvent.geofence_id == geofence_id)
        .order_by(GeofenceEvent.occurred_at.desc(), GeofenceEvent.id.desc())
        .limit(500)
        .all()
    )


@router.get("/locations/history", response_model=list[DeviceLocationRead])
def location_history(device_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(LocationEvent).order_by(LocationEvent.recorded_at.desc(), LocationEvent.id.desc())
    if device_id:
        query = query.filter(LocationEvent.device_id == device_id)
    return query.limit(500).all()

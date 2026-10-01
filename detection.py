from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models import Device, EventType, Geofence, GeofenceEvent, LocationEvent
from app.schemas import LocationIngest
from app.services.geo import Point, is_inside_geofence


def get_or_create_device(db: Session, identifier: str) -> Device:
    device = db.query(Device).filter(Device.identifier == identifier).one_or_none()
    if device:
        return device
    device = Device(identifier=identifier)
    db.add(device)
    db.flush()
    return device


def previous_state_for(db: Session, device_id: int, geofence_id: int) -> str | None:
    latest = (
        db.query(GeofenceEvent)
        .filter(GeofenceEvent.device_id == device_id, GeofenceEvent.geofence_id == geofence_id)
        .order_by(desc(GeofenceEvent.occurred_at), desc(GeofenceEvent.id))
        .first()
    )
    return latest.current_state if latest else None


def classify_event(previous_state: str | None, current_state: str, geofence: Geofence) -> EventType | None:
    if previous_state is None:
        if current_state == "inside" and geofence.emit_inside_events:
            return EventType.inside
        if current_state == "outside":
            return EventType.outside
        return None
    if previous_state == "outside" and current_state == "inside":
        return EventType.enter
    if previous_state == "inside" and current_state == "outside":
        return EventType.exit
    if current_state == "inside" and geofence.emit_inside_events:
        return EventType.inside
    if current_state == "outside" and geofence.emit_outside_events:
        return EventType.outside
    return None


def ingest_location(db: Session, payload: LocationIngest) -> tuple[LocationEvent, list[GeofenceEvent]]:
    device = get_or_create_device(db, payload.device_identifier)
    location = LocationEvent(
        device_id=device.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy_meters=payload.accuracy_meters,
        recorded_at=payload.timestamp,
    )
    db.add(location)
    db.flush()

    generated: list[GeofenceEvent] = []
    point = Point(payload.latitude, payload.longitude)
    geofences = db.query(Geofence).filter(Geofence.is_enabled.is_(True)).all()
    for geofence in geofences:
        current_state = "inside" if is_inside_geofence(geofence, point, payload.accuracy_meters) else "outside"
        previous_state = previous_state_for(db, device.id, geofence.id)
        event_type = classify_event(previous_state, current_state, geofence)
        if event_type is None:
            continue
        event = GeofenceEvent(
            location_event_id=location.id,
            device_id=device.id,
            geofence_id=geofence.id,
            event_type=event_type,
            previous_state=previous_state,
            current_state=current_state,
            latitude=payload.latitude,
            longitude=payload.longitude,
            occurred_at=payload.timestamp,
        )
        db.add(event)
        generated.append(event)
    db.commit()
    db.refresh(location)
    for event in generated:
        db.refresh(event)
    return location, generated

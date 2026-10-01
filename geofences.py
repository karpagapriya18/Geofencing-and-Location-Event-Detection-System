from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AuditLog, Geofence, GeofencePoint
from app.schemas import GeofenceCreate, GeofenceRead, GeofenceUpdate

router = APIRouter(prefix="/geofences", tags=["geofences"])


def serialize_geofence(geofence: Geofence) -> GeofenceRead:
    data = GeofenceRead.model_validate(geofence)
    data.points = [{"latitude": p.latitude, "longitude": p.longitude} for p in geofence.points]
    return data


@router.get("", response_model=list[GeofenceRead])
def list_geofences(db: Session = Depends(get_db)):
    return [serialize_geofence(item) for item in db.query(Geofence).all()]


@router.post("", response_model=GeofenceRead, status_code=status.HTTP_201_CREATED)
def create_geofence(payload: GeofenceCreate, db: Session = Depends(get_db)):
    geofence = Geofence(**payload.model_dump(exclude={"points"}))
    db.add(geofence)
    db.flush()
    for index, point in enumerate(payload.points):
        db.add(GeofencePoint(geofence_id=geofence.id, sequence=index, latitude=point.latitude, longitude=point.longitude))
    db.add(AuditLog(action="create", entity_type="geofence", entity_id=geofence.id, details=payload.model_dump_json()))
    db.commit()
    db.refresh(geofence)
    return serialize_geofence(geofence)


@router.get("/{geofence_id}", response_model=GeofenceRead)
def get_geofence(geofence_id: int, db: Session = Depends(get_db)):
    geofence = db.get(Geofence, geofence_id)
    if not geofence:
        raise HTTPException(status_code=404, detail="Geofence not found")
    return serialize_geofence(geofence)


@router.patch("/{geofence_id}", response_model=GeofenceRead)
def update_geofence(geofence_id: int, payload: GeofenceUpdate, db: Session = Depends(get_db)):
    geofence = db.get(Geofence, geofence_id)
    if not geofence:
        raise HTTPException(status_code=404, detail="Geofence not found")
    updates = payload.model_dump(exclude_unset=True, exclude={"points"})
    for key, value in updates.items():
        setattr(geofence, key, value)
    if payload.points is not None:
        geofence.points.clear()
        db.flush()
        for index, point in enumerate(payload.points):
            db.add(GeofencePoint(geofence_id=geofence.id, sequence=index, latitude=point.latitude, longitude=point.longitude))
    db.add(AuditLog(action="update", entity_type="geofence", entity_id=geofence.id, details=payload.model_dump_json()))
    db.commit()
    db.refresh(geofence)
    return serialize_geofence(geofence)


@router.delete("/{geofence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_geofence(geofence_id: int, db: Session = Depends(get_db)):
    geofence = db.get(Geofence, geofence_id)
    if not geofence:
        raise HTTPException(status_code=404, detail="Geofence not found")
    db.delete(geofence)
    db.add(AuditLog(action="delete", entity_type="geofence", entity_id=geofence_id))
    db.commit()

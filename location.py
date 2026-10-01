from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import EventType


class LocationIngest(BaseModel):
    device_identifier: str = Field(min_length=1, max_length=120)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timestamp: datetime
    accuracy_meters: float | None = Field(default=None, ge=0, le=5000)


class GeofenceEventRead(BaseModel):
    id: int
    device_id: int
    geofence_id: int
    event_type: EventType
    previous_state: str | None
    current_state: str
    latitude: float
    longitude: float
    occurred_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LocationIngestResponse(BaseModel):
    location_event_id: int
    generated_events: list[GeofenceEventRead]


class DeviceLocationRead(BaseModel):
    id: int
    device_id: int
    latitude: float
    longitude: float
    accuracy_meters: float | None
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)

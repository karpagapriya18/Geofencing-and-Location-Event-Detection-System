from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import BoundaryType


class Coordinate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    model_config = ConfigDict(from_attributes=True)


class GeofenceBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None
    boundary_type: BoundaryType
    is_enabled: bool = True
    center_lat: float | None = Field(default=None, ge=-90, le=90)
    center_lng: float | None = Field(default=None, ge=-180, le=180)
    radius_meters: float | None = Field(default=None, gt=0)
    accuracy_buffer_meters: float = Field(default=15, ge=0, le=250)
    emit_inside_events: bool = True
    emit_outside_events: bool = False
    points: list[Coordinate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_boundary(self):
        if self.boundary_type == BoundaryType.circle:
            if self.center_lat is None or self.center_lng is None or self.radius_meters is None:
                raise ValueError("circle geofences require center_lat, center_lng, and radius_meters")
        if self.boundary_type == BoundaryType.polygon and len(self.points) < 3:
            raise ValueError("polygon geofences require at least three points")
        return self


class GeofenceCreate(GeofenceBase):
    pass


class GeofenceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = None
    is_enabled: bool | None = None
    center_lat: float | None = Field(default=None, ge=-90, le=90)
    center_lng: float | None = Field(default=None, ge=-180, le=180)
    radius_meters: float | None = Field(default=None, gt=0)
    accuracy_buffer_meters: float | None = Field(default=None, ge=0, le=250)
    emit_inside_events: bool | None = None
    emit_outside_events: bool | None = None
    points: list[Coordinate] | None = None


class GeofenceRead(GeofenceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

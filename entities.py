import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class BoundaryType(str, enum.Enum):
    circle = "circle"
    polygon = "polygon"


class EventType(str, enum.Enum):
    enter = "enter"
    exit = "exit"
    inside = "inside"
    outside = "outside"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(40), default="admin")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    devices: Mapped[list["Device"]] = relationship(back_populates="user")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    identifier: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    label: Mapped[str | None] = mapped_column(String(120))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped[User | None] = relationship(back_populates="devices")
    events: Mapped[list["LocationEvent"]] = relationship(back_populates="device")


class Geofence(Base):
    __tablename__ = "geofences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    boundary_type: Mapped[BoundaryType] = mapped_column(Enum(BoundaryType), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    center_lat: Mapped[float | None] = mapped_column(Float)
    center_lng: Mapped[float | None] = mapped_column(Float)
    radius_meters: Mapped[float | None] = mapped_column(Float)
    accuracy_buffer_meters: Mapped[float] = mapped_column(Float, default=15.0)
    emit_inside_events: Mapped[bool] = mapped_column(Boolean, default=True)
    emit_outside_events: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    points: Mapped[list["GeofencePoint"]] = relationship(
        back_populates="geofence", cascade="all, delete-orphan", order_by="GeofencePoint.sequence"
    )


class GeofencePoint(Base):
    __tablename__ = "geofence_points"
    __table_args__ = (UniqueConstraint("geofence_id", "sequence", name="uq_geofence_point_sequence"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    geofence_id: Mapped[int] = mapped_column(ForeignKey("geofences.id", ondelete="CASCADE"), index=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    geofence: Mapped[Geofence] = relationship(back_populates="points")


class LocationEvent(Base):
    __tablename__ = "location_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy_meters: Mapped[float | None] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    device: Mapped[Device] = relationship(back_populates="events")
    geofence_events: Mapped[list["GeofenceEvent"]] = relationship(back_populates="location_event")


class GeofenceEvent(Base):
    __tablename__ = "geofence_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location_event_id: Mapped[int] = mapped_column(ForeignKey("location_events.id"), index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    geofence_id: Mapped[int] = mapped_column(ForeignKey("geofences.id"), index=True)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False, index=True)
    previous_state: Mapped[str | None] = mapped_column(String(20))
    current_state: Mapped[str] = mapped_column(String(20), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    location_event: Mapped[LocationEvent] = relationship(back_populates="geofence_events")
    geofence: Mapped[Geofence] = relationship()
    device: Mapped[Device] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor: Mapped[str] = mapped_column(String(120), default="system")
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer)
    details: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

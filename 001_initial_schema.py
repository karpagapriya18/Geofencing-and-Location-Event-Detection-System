"""initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-10-01
"""

from alembic import op
import sqlalchemy as sa

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

boundary_type = sa.Enum("circle", "polygon", name="boundarytype")
event_type = sa.Enum("enter", "exit", "inside", "outside", name="eventtype")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=40), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("identifier", sa.String(length=120), nullable=False, unique=True),
        sa.Column("label", sa.String(length=120), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "geofences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("boundary_type", boundary_type, nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("center_lat", sa.Float(), nullable=True),
        sa.Column("center_lng", sa.Float(), nullable=True),
        sa.Column("radius_meters", sa.Float(), nullable=True),
        sa.Column("accuracy_buffer_meters", sa.Float(), nullable=False),
        sa.Column("emit_inside_events", sa.Boolean(), nullable=False),
        sa.Column("emit_outside_events", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "geofence_points",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("geofence_id", sa.Integer(), sa.ForeignKey("geofences.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.UniqueConstraint("geofence_id", "sequence", name="uq_geofence_point_sequence"),
    )
    op.create_table(
        "location_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("accuracy_meters", sa.Float(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "geofence_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("location_event_id", sa.Integer(), sa.ForeignKey("location_events.id"), nullable=False),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("geofence_id", sa.Integer(), sa.ForeignKey("geofences.id"), nullable=False),
        sa.Column("event_type", event_type, nullable=False),
        sa.Column("previous_state", sa.String(length=20), nullable=True),
        sa.Column("current_state", sa.String(length=20), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor", sa.String(length=120), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for table, column in [
        ("devices", "identifier"),
        ("geofences", "name"),
        ("location_events", "recorded_at"),
        ("geofence_events", "occurred_at"),
    ]:
        op.create_index(f"ix_{table}_{column}", table, [column])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("geofence_events")
    op.drop_table("location_events")
    op.drop_table("geofence_points")
    op.drop_table("geofences")
    op.drop_table("devices")
    op.drop_table("users")
    event_type.drop(op.get_bind(), checkfirst=True)
    boundary_type.drop(op.get_bind(), checkfirst=True)

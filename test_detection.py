from app.models import BoundaryType, EventType, Geofence
from app.services.detection import classify_event


def fence():
    return Geofence(name="test", boundary_type=BoundaryType.circle, emit_inside_events=True, emit_outside_events=False)


def test_enter_event_when_previous_outside():
    assert classify_event("outside", "inside", fence()) == EventType.enter


def test_exit_event_when_previous_inside():
    assert classify_event("inside", "outside", fence()) == EventType.exit


def test_no_duplicate_outside_when_disabled():
    assert classify_event("outside", "outside", fence()) is None


def test_initial_outside_state_is_recorded():
    assert classify_event(None, "outside", fence()) == EventType.outside


def test_inside_heartbeat_when_enabled():
    assert classify_event("inside", "inside", fence()) == EventType.inside

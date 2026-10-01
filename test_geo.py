from app.models import BoundaryType, Geofence, GeofencePoint
from app.services.geo import Point, haversine_distance_m, is_inside_geofence, point_in_polygon


def test_haversine_distance_close_to_one_km():
    distance = haversine_distance_m(Point(0, 0), Point(0, 0.008993))
    assert 990 <= distance <= 1010


def test_circle_boundary_uses_accuracy_buffer():
    fence = Geofence(
        name="HQ",
        boundary_type=BoundaryType.circle,
        center_lat=0,
        center_lng=0,
        radius_meters=100,
        accuracy_buffer_meters=10,
    )
    assert is_inside_geofence(fence, Point(0, 0.00099), accuracy_meters=5)


def test_polygon_contains_point_and_rejects_outside():
    square = [Point(0, 0), Point(0, 1), Point(1, 1), Point(1, 0)]
    assert point_in_polygon(Point(0.5, 0.5), square)
    assert not point_in_polygon(Point(1.5, 0.5), square)


def test_polygon_boundary_buffer_counts_as_inside():
    fence = Geofence(name="yard", boundary_type=BoundaryType.polygon, accuracy_buffer_meters=25)
    fence.points = [
        GeofencePoint(sequence=0, latitude=0, longitude=0),
        GeofencePoint(sequence=1, latitude=0, longitude=0.01),
        GeofencePoint(sequence=2, latitude=0.01, longitude=0.01),
        GeofencePoint(sequence=3, latitude=0.01, longitude=0),
    ]
    assert is_inside_geofence(fence, Point(-0.0001, 0.005))

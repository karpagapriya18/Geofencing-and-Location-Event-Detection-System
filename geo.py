import math
from dataclasses import dataclass

from app.models import BoundaryType, Geofence

EARTH_RADIUS_M = 6_371_000


@dataclass(frozen=True)
class Point:
    latitude: float
    longitude: float


def haversine_distance_m(a: Point, b: Point) -> float:
    lat1 = math.radians(a.latitude)
    lat2 = math.radians(b.latitude)
    dlat = math.radians(b.latitude - a.latitude)
    dlng = math.radians(b.longitude - a.longitude)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))


def point_in_polygon(point: Point, polygon: list[Point]) -> bool:
    inside = False
    j = len(polygon) - 1
    for i, current in enumerate(polygon):
        previous = polygon[j]
        intersects = (
            (current.longitude > point.longitude) != (previous.longitude > point.longitude)
            and point.latitude
            < (previous.latitude - current.latitude)
            * (point.longitude - current.longitude)
            / ((previous.longitude - current.longitude) or 1e-12)
            + current.latitude
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def distance_to_segment_m(point: Point, a: Point, b: Point) -> float:
    mean_lat = math.radians((a.latitude + b.latitude + point.latitude) / 3)

    def project(p: Point) -> tuple[float, float]:
        x = math.radians(p.longitude) * math.cos(mean_lat) * EARTH_RADIUS_M
        y = math.radians(p.latitude) * EARTH_RADIUS_M
        return x, y

    px, py = project(point)
    ax, ay = project(a)
    bx, by = project(b)
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def near_polygon_boundary(point: Point, polygon: list[Point], buffer_meters: float) -> bool:
    return any(distance_to_segment_m(point, a, polygon[(i + 1) % len(polygon)]) <= buffer_meters for i, a in enumerate(polygon))


def is_inside_geofence(geofence: Geofence, point: Point, accuracy_meters: float | None = None) -> bool:
    buffer = geofence.accuracy_buffer_meters + (accuracy_meters or 0)
    if geofence.boundary_type == BoundaryType.circle:
        center = Point(geofence.center_lat or 0, geofence.center_lng or 0)
        return haversine_distance_m(center, point) <= (geofence.radius_meters or 0) + buffer
    polygon = [Point(p.latitude, p.longitude) for p in geofence.points]
    return point_in_polygon(point, polygon) or near_polygon_boundary(point, polygon, buffer)

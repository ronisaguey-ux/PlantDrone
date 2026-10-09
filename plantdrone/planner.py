"""Module A: lawnmower (boustrophedon) waypoint generator."""
import json
from dataclasses import dataclass
from typing import List, Sequence, Tuple

from shapely.geometry import LineString, Polygon

from .geo import LocalFrame


@dataclass(frozen=True)
class Waypoint:
    lat: float
    lon: float
    alt: float


def load_boundary(path: str) -> List[Tuple[float, float]]:
    """Load a boundary as [(lat, lon), ...] from GeoJSON (Polygon/Feature/FeatureCollection)."""
    with open(path) as f:
        obj = json.load(f)
    if obj["type"] == "FeatureCollection":
        obj = obj["features"][0]
    if obj["type"] == "Feature":
        obj = obj["geometry"]
    if obj["type"] != "Polygon":
        raise ValueError("GeoJSON must contain a Polygon")
    ring = obj["coordinates"][0]  # GeoJSON is [lon, lat]
    return [(lat, lon) for lon, lat in ring]


def generate_lawnmower(boundary: Sequence[Tuple[float, float]], altitude: float = 10.0,
                       spacing: float = 5.0) -> List[Waypoint]:
    """Generate east-west sweep waypoints inside `boundary` ((lat, lon) pairs).

    spacing is the distance in meters between adjacent passes.
    """
    if spacing <= 0:
        raise ValueError("spacing must be > 0")
    if len(boundary) < 3:
        raise ValueError("boundary needs at least 3 points")
    frame = LocalFrame(*boundary[0])
    poly = Polygon([frame.to_xy(la, lo) for la, lo in boundary])
    if not poly.is_valid:
        poly = poly.buffer(0)
    minx, miny, maxx, maxy = poly.bounds

    waypoints: List[Waypoint] = []
    y, flip = miny + spacing / 2, False
    while y < maxy:
        inter = poly.intersection(LineString([(minx - 1, y), (maxx + 1, y)]))
        segs = [inter] if inter.geom_type == "LineString" else list(getattr(inter, "geoms", []))
        segs = sorted((s for s in segs if s.geom_type == "LineString" and s.length > 0),
                      key=lambda s: s.bounds[0], reverse=flip)
        for s in segs:
            xs = sorted((s.coords[0], s.coords[-1]))
            a, b = (xs[1], xs[0]) if flip else (xs[0], xs[1])
            for x, yy in (a, b):
                lat, lon = frame.to_latlon(x, yy)
                waypoints.append(Waypoint(lat, lon, altitude))
        if segs:
            flip = not flip
        y += spacing
    return waypoints

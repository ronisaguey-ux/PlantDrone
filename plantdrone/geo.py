"""Local equirectangular projection helpers (accurate for farm-scale areas)."""
import math

EARTH_R = 6371008.8


class LocalFrame:
    """Meters east/north relative to an origin lat/lon."""

    def __init__(self, lat0: float, lon0: float):
        self.lat0, self.lon0 = lat0, lon0
        self._kx = math.radians(1) * EARTH_R * math.cos(math.radians(lat0))
        self._ky = math.radians(1) * EARTH_R

    def to_xy(self, lat, lon):
        return (lon - self.lon0) * self._kx, (lat - self.lat0) * self._ky

    def to_latlon(self, x, y):
        return self.lat0 + y / self._ky, self.lon0 + x / self._kx


def distance_m(lat1, lon1, lat2, lon2) -> float:
    """Haversine ground distance in meters."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_R * math.asin(math.sqrt(a))

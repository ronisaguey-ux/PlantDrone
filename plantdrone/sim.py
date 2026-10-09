"""Offline flight simulation: fly waypoints at 10 Hz through SprayController (no PX4 needed)."""
import math
from typing import List, Sequence, Tuple

from .geo import LocalFrame
from .planner import Waypoint
from .sprayer import SprayController


def simulate(wps: Sequence[Waypoint], ctl: SprayController, hz: float = 10.0) -> List[int]:
    """Return target indices sprayed, in order. Drone speed follows ctl's commanded speed."""
    frame = LocalFrame(wps[0].lat, wps[0].lon)
    pts = [frame.to_xy(w.lat, w.lon) for w in wps]
    x, y = pts[0]
    speed, hits = ctl.cruise_speed, []
    for tx, ty in pts[1:]:
        while True:
            d = math.hypot(tx - x, ty - y)
            step = speed / hz
            if d <= step:
                x, y = tx, ty
                break
            x += (tx - x) / d * step
            y += (ty - y) / d * step
            _, speed, hit = ctl.update(*frame.to_latlon(x, y))
            if hit is not None:
                hits.append(hit)
    return hits

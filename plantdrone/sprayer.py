"""Module C: proximity-triggered spot spraying logic."""
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Set, Tuple

from .geo import distance_m

TRIGGER_RADIUS_M = 1.5


def load_targets(path: str) -> List[Tuple[float, float]]:
    """CSV/plain text lines of 'lat,lon' (blank lines and # comments ignored)."""
    out = []
    with open(path) as f:
        for line in f:
            line = line.split("#")[0].strip()
            if line:
                la, lo = line.split(",")[:2]
                out.append((float(la), float(lo)))
    return out


@dataclass
class SprayController:
    targets: List[Tuple[float, float]]
    trigger_radius: float = TRIGGER_RADIUS_M
    slow_radius: float = 5.0
    cruise_speed: float = 5.0
    spray_speed: float = 1.0
    sprayed: Set[int] = field(default_factory=set)
    pump_on: bool = False

    def nearest(self, lat, lon) -> Tuple[Optional[int], float]:
        """Nearest not-yet-sprayed target index and its distance."""
        best, bd = None, float("inf")
        for i, (tl, tn) in enumerate(self.targets):
            if i in self.sprayed:
                continue
            d = distance_m(lat, lon, tl, tn)
            if d < bd:
                best, bd = i, d
        return best, bd

    def update(self, lat, lon):
        """Return (pump_on, speed, newly_sprayed_index_or_None) for this position."""
        idx, d = self.nearest(lat, lon)
        if idx is not None and d < self.trigger_radius:
            self.pump_on = True
            self.sprayed.add(idx)
            return True, self.spray_speed, idx
        # keep pump on while still inside radius of the target just sprayed
        if self.pump_on and any(distance_m(lat, lon, *self.targets[i]) < self.trigger_radius
                                for i in self.sprayed):
            return True, self.spray_speed, None
        self.pump_on = False
        if idx is not None and d < self.slow_radius:
            return False, self.spray_speed, None
        return False, self.cruise_speed, None

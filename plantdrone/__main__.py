import argparse
import asyncio

from .planner import generate_lawnmower, load_boundary
from .sprayer import SprayController, load_targets


def main():
    ap = argparse.ArgumentParser(prog="plantdrone")
    ap.add_argument("--boundary", default="data/field.geojson")
    ap.add_argument("--targets", default="data/targets.csv")
    ap.add_argument("--altitude", type=float, default=10.0)
    ap.add_argument("--spacing", type=float, default=5.0)
    ap.add_argument("--address", default="udp://:14540")
    ap.add_argument("--dry-run", action="store_true", help="print waypoints, don't fly")
    a = ap.parse_args()

    wps = generate_lawnmower(load_boundary(a.boundary), a.altitude, a.spacing)
    print(f"Generated {len(wps)} waypoints")
    if a.dry_run:
        for w in wps:
            print(f"{w.lat:.7f},{w.lon:.7f},{w.alt}")
        return
    from .flight import connect, fly
    ctl = SprayController(load_targets(a.targets))

    async def run():
        await fly(await connect(a.address), wps, ctl)
    asyncio.run(run())


main()

# PlantDrone

Autonomous lawnmower survey + Variable-Rate Application (VRA) spot spraying via PX4 SITL and MAVSDK.

Flow: field boundary → waypoint generator → MAVSDK flight → GPS proximity trigger → spray relay signal.

| Module | File | Role |
|---|---|---|
| A | `plantdrone/planner.py` | GeoJSON/lat-lon polygon → serpentine waypoints at fixed altitude (shapely) |
| B | `plantdrone/flight.py` | Connect `udp://:14540`, arm, upload/start mission, stream lat/lon/alt |
| C | `plantdrone/sprayer.py` | Within 1.5 m of a target: pump actuator ON (`set_actuator`) and slow to 1 m/s |

## Run
```
pip install -r requirements.txt
python -m plantdrone --dry-run          # print waypoints only
make px4_sitl gz_x500                   # in PX4-Autopilot, then:
python -m plantdrone --altitude 10 --spacing 5
pytest
```
Edit `data/field.geojson` and `data/targets.csv` (`lat,lon` per line). Defaults match PX4 SITL's Zurich home.
Note: the actuator index (`SPRAY_ACTUATOR_INDEX` in `flight.py`) must be mapped to an output in your PX4 airframe.

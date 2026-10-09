"""Module B: MAVSDK flight execution, telemetry streaming and spray loop."""
import asyncio
from typing import List

from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan

from .planner import Waypoint
from .sprayer import SprayController

SPRAY_ACTUATOR_INDEX = 1  # relay/valve output channel


async def connect(address: str = "udp://:14540") -> System:
    drone = System()
    await drone.connect(system_address=address)
    async for s in drone.core.connection_state():
        if s.is_connected:
            break
    async for h in drone.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            break
    return drone


def to_mission(wps: List[Waypoint]) -> MissionPlan:
    """Speed is NaN (unchanged) so runtime set_current_speed isn't reset per waypoint."""
    nan = float("nan")
    items = [MissionItem(w.lat, w.lon, w.alt, nan, True, nan, nan,
                         MissionItem.CameraAction.NONE, nan, nan, nan, nan, nan,
                         MissionItem.VehicleAction.NONE) for w in wps]
    return MissionPlan(items)


async def spray_loop(drone: System, ctl: SprayController, mission_done: asyncio.Event):
    """Stream position; actuate the pump and adjust speed on proximity."""
    last_speed, last_pump = None, False
    await drone.telemetry.set_rate_position(10.0)  # 10 Hz so a 1.5 m zone isn't skipped
    async for pos in drone.telemetry.position():
        print(f"pos lat={pos.latitude_deg:.7f} lon={pos.longitude_deg:.7f} "
              f"alt={pos.relative_altitude_m:.1f}m")
        pump, speed, hit = ctl.update(pos.latitude_deg, pos.longitude_deg)
        if hit is not None:
            print(f"*** SPRAY target #{hit} {ctl.targets[hit]} ***")
        if pump != last_pump:
            await drone.action.set_actuator(SPRAY_ACTUATOR_INDEX, 1.0 if pump else 0.0)
            print("PUMP", "ON" if pump else "OFF")
            last_pump = pump
        if speed != last_speed:
            await drone.action.set_current_speed(speed)
            last_speed = speed
        if mission_done.is_set():
            break


async def fly(drone: System, wps: List[Waypoint], ctl: SprayController):
    await drone.mission.set_return_to_launch_after_mission(True)
    await drone.mission.upload_mission(to_mission(wps))
    await drone.action.set_current_speed(ctl.cruise_speed)
    await drone.action.arm()
    done = asyncio.Event()
    task = asyncio.create_task(spray_loop(drone, ctl, done))
    await drone.mission.start_mission()  # auto-takeoff + execute
    async for p in drone.mission.mission_progress():
        print(f"mission {p.current}/{p.total}")
        if p.total and p.current == p.total:
            break
    done.set()
    await drone.action.set_actuator(SPRAY_ACTUATOR_INDEX, 0.0)
    await task

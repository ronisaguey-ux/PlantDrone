from plantdrone.geo import distance_m
from plantdrone.planner import generate_lawnmower, load_boundary
from plantdrone.sprayer import SprayController

B = load_boundary("data/field.geojson")


def test_waypoints_inside_and_alt():
    wps = generate_lawnmower(B, 10, 5)
    assert len(wps) >= 20 and len(wps) % 2 == 0
    assert all(w.alt == 10 for w in wps)
    assert all(47.3976 < w.lat < 47.3988 and 8.5454 < w.lon < 8.5471 for w in wps)


def test_serpentine_alternates():
    w = generate_lawnmower(B, 10, 5)
    assert w[0].lon < w[1].lon and w[2].lon > w[3].lon


def test_spray_trigger():
    c = SprayController([(47.0, 8.0)])
    assert c.update(47.0 + 3 / 111320, 8.0)[0] is False
    pump, speed, hit = c.update(47.0 + 1 / 111320, 8.0)
    assert pump and hit == 0 and speed == c.spray_speed
    assert c.update(47.001, 8.0)[0] is False
    assert distance_m(47, 8, 47.001, 8) > 100


def test_simulated_flight_hits_all_targets():
    from plantdrone.sim import simulate
    from plantdrone.sprayer import load_targets
    wps = generate_lawnmower(B, 10, 3)
    ctl = SprayController(load_targets("data/targets.csv"))
    assert sorted(simulate(wps, ctl)) == [0, 1, 2]

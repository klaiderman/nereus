import math

import pytest

from nereus.geo import dead_reckon, haversine_m


def test_haversine_one_degree_of_longitude_at_equator():
    assert haversine_m(0.0, 0.0, 0.0, 1.0) == pytest.approx(111_194.9, abs=1.0)


def test_dead_reckon_due_north_moves_latitude_only():
    lat, lon = dead_reckon(0.0, 0.0, sog_knots=100.0, cog_deg=0.0, dt_s=60.0)
    assert lat > 0.0
    assert lon == pytest.approx(0.0, abs=1e-9)


def test_dead_reckon_due_east_moves_longitude_only():
    lat, lon = dead_reckon(0.0, 0.0, sog_knots=100.0, cog_deg=90.0, dt_s=60.0)
    assert lon > 0.0
    assert lat == pytest.approx(0.0, abs=1e-9)


def test_dead_reckon_is_stationary_at_zero_speed():
    assert dead_reckon(31.8, 34.6, sog_knots=0.0, cog_deg=45.0, dt_s=120.0) == (31.8, 34.6)


def test_haversine_survives_near_antipodal_points():
    # Float drift can push the asin argument just above 1.0 here; clamped, it must not raise.
    distance = haversine_m(
        57.572254532564585, 78.01032232096884, -57.57225453271766, -101.98967767975745
    )
    assert math.isfinite(distance)


def test_dead_reckon_at_the_pole_stays_in_range():
    lat, lon = dead_reckon(90.0, 0.0, sog_knots=10.0, cog_deg=90.0, dt_s=60.0)
    assert -90.0 <= lat <= 90.0
    assert -180.0 <= lon <= 180.0

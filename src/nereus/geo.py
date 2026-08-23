import math

EARTH_RADIUS_M = 6_371_000.0
KNOTS_TO_MPS = 0.514444


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points, in metres."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    # Clamp against floating-point drift above 1.0 for near-antipodal points, which
    # would otherwise push asin outside its domain and raise.
    return 2 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(a)))


def dead_reckon(
    lat: float, lon: float, sog_knots: float, cog_deg: float, dt_s: float
) -> tuple[float, float]:
    """Project a position along its course by dt seconds.

    AIS arrives far more sparsely than camera frames, so a report is almost never
    stamped at the frame time. Advancing it along its own course/speed is what lets a
    stale track still line up with a live detection instead of looking like a mismatch.
    """
    distance_m = sog_knots * KNOTS_TO_MPS * dt_s
    if distance_m == 0.0:
        return lat, lon
    bearing = math.radians(cog_deg)
    dlat = (distance_m * math.cos(bearing)) / EARTH_RADIUS_M
    cos_lat = math.cos(math.radians(lat))
    # At the poles cos(lat) -> 0; longitude is meaningless there, so hold it.
    dlon = 0.0 if abs(cos_lat) < 1e-12 else (distance_m * math.sin(bearing)) / (EARTH_RADIUS_M * cos_lat)
    return _clamp_lat(lat + math.degrees(dlat)), _wrap_lon(lon + math.degrees(dlon))


def _clamp_lat(lat: float) -> float:
    return max(-90.0, min(90.0, lat))


def _wrap_lon(lon: float) -> float:
    return ((lon + 180.0) % 360.0) - 180.0

import math

EARTH_RADIUS_M = 6_371_000.0
KNOTS_TO_MPS = 0.514444


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points, in metres."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def dead_reckon(lat, lon, sog_knots, cog_deg, dt_s):
    """Project a position along its course by dt seconds."""
    distance_m = sog_knots * KNOTS_TO_MPS * dt_s
    if distance_m == 0.0:
        return lat, lon
    bearing = math.radians(cog_deg)
    dlat = (distance_m * math.cos(bearing)) / EARTH_RADIUS_M
    dlon = (distance_m * math.sin(bearing)) / (EARTH_RADIUS_M * math.cos(math.radians(lat)))
    return lat + math.degrees(dlat), lon + math.degrees(dlon)

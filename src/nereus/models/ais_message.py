from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AisMessage:
    """A decoded AIS position report. Speed is knots, course is degrees true."""

    timestamp: float
    mmsi: int
    lat: float
    lon: float
    sog: float
    cog: float
    ship_type: int
    length_m: float

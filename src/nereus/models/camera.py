import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Camera:
    """A shore camera's coverage, modelled as a range circle around its position.

    Used to gate AIS ghosts: an AIS track only counts as 'unseen' if it lies inside an
    area a camera actually watches. A real deployment carries a full viewshed (bearing
    wedge, terrain occlusion, range curve); a circle is a coarse stand-in for the slice.
    """

    camera_id: str
    lat: float
    lon: float
    range_m: float

    def __post_init__(self) -> None:
        if not (math.isfinite(self.lat) and -90.0 <= self.lat <= 90.0):
            raise ValueError("camera lat out of range")
        if not (math.isfinite(self.lon) and -180.0 <= self.lon <= 180.0):
            raise ValueError("camera lon out of range")
        if not self.range_m > 0.0:
            raise ValueError("camera range_m must be > 0")

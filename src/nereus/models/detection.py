from dataclasses import dataclass

from nereus.enums import SensorType, VesselClass


@dataclass(frozen=True, slots=True)
class Detection:
    """A single vessel seen by the vision pipeline, already geo-referenced."""

    timestamp: float
    det_id: str
    camera_id: str
    lat: float
    lon: float
    vessel_class: VesselClass
    length_m: float
    heading: float
    confidence: float
    sensor: SensorType

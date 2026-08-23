from dataclasses import dataclass

from nereus.models.ais_message import AisMessage
from nereus.models.detection import Detection


@dataclass(frozen=True, slots=True)
class MatchedPair:
    """A detection the associator bound to an AIS track, and how far apart they sat."""

    detection: Detection
    ais: AisMessage
    distance_m: float

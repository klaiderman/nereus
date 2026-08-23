from dataclasses import dataclass

from nereus.models.ais_message import AisMessage
from nereus.models.detection import Detection
from nereus.models.matched_pair import MatchedPair


@dataclass(frozen=True, slots=True)
class MatchResult:
    """The three exhaustive outcomes of one association pass over a frame."""

    frame_ts: float
    matched: tuple[MatchedPair, ...]
    unmatched_detections: tuple[Detection, ...]
    unmatched_ais: tuple[AisMessage, ...]

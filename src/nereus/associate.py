import numpy as np
from scipy.optimize import linear_sum_assignment

from nereus.config import FusionConfig
from nereus.geo import haversine_m
from nereus.ingest import projected_position
from nereus.models.ais_message import AisMessage
from nereus.models.detection import Detection
from nereus.models.match_result import MatchResult
from nereus.models.matched_pair import MatchedPair

# Forbidden-but-finite cost for pairs beyond the gate. Keeps the assignment from
# preferring an out-of-gate pairing, without the inf that makes scipy raise.
_OVER_GATE_COST = 1e12


def associate(
    detections: list[Detection],
    ais_messages: list[AisMessage],
    frame_ts: float,
    config: FusionConfig,
) -> MatchResult:
    """Bind detections to AIS tracks by optimal assignment under a distance gate.

    Stateless: one frame in, one partition out (matched pairs, unclaimed detections,
    unseen AIS). Inputs are sorted so equal-cost ties resolve deterministically, and the
    gate is baked into the cost matrix so assignment doesn't pick a pair it would then
    discard.
    """
    if not detections or not ais_messages:
        return MatchResult(frame_ts, (), tuple(detections), tuple(ais_messages))

    detections = sorted(detections, key=lambda det: det.det_id)
    ais_messages = sorted(ais_messages, key=lambda ais: ais.mmsi)

    projected = [projected_position(ais, frame_ts, config) for ais in ais_messages]
    cost = np.array(
        [
            [_gated_cost(haversine_m(det.lat, det.lon, lat, lon), config) for lat, lon in projected]
            for det in detections
        ]
    )
    rows, cols = linear_sum_assignment(cost)

    matched: list[MatchedPair] = []
    claimed_detections: set[int] = set()
    claimed_ais: set[int] = set()
    for row, col in zip(rows, cols):
        distance_m = haversine_m(detections[row].lat, detections[row].lon, *projected[col])
        if distance_m <= config.gate_radius_m:
            matched.append(MatchedPair(detections[row], ais_messages[col], distance_m))
            claimed_detections.add(row)
            claimed_ais.add(col)

    unmatched_detections = tuple(
        det for i, det in enumerate(detections) if i not in claimed_detections
    )
    unmatched_ais = tuple(ais for j, ais in enumerate(ais_messages) if j not in claimed_ais)
    return MatchResult(frame_ts, tuple(matched), unmatched_detections, unmatched_ais)


def _gated_cost(distance_m: float, config: FusionConfig) -> float:
    return distance_m if distance_m <= config.gate_radius_m else _OVER_GATE_COST

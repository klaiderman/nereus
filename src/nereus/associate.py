import numpy as np
from scipy.optimize import linear_sum_assignment

from nereus.config import FusionConfig
from nereus.geo import dead_reckon, haversine_m
from nereus.models.ais_message import AisMessage
from nereus.models.detection import Detection
from nereus.models.match_result import MatchResult
from nereus.models.matched_pair import MatchedPair


def associate(detections, ais_messages, frame_ts, config):
    """Bind detections to AIS tracks by optimal assignment under a distance gate."""
    if not detections or not ais_messages:
        return MatchResult(frame_ts, (), tuple(detections), tuple(ais_messages))

    projected = [
        dead_reckon(a.lat, a.lon, a.sog, a.cog, frame_ts - a.timestamp) for a in ais_messages
    ]
    cost = np.array(
        [[haversine_m(d.lat, d.lon, lat, lon) for lat, lon in projected] for d in detections]
    )
    rows, cols = linear_sum_assignment(cost)

    matched, claimed_d, claimed_a = [], set(), set()
    for r, col in zip(rows, cols):
        distance_m = float(cost[r, col])
        if distance_m <= config.gate_radius_m:
            matched.append(MatchedPair(detections[r], ais_messages[col], distance_m))
            claimed_d.add(r)
            claimed_a.add(col)

    unmatched_d = tuple(d for i, d in enumerate(detections) if i not in claimed_d)
    unmatched_a = tuple(a for j, a in enumerate(ais_messages) if j not in claimed_a)
    return MatchResult(frame_ts, tuple(matched), unmatched_d, unmatched_a)

from nereus.associate import associate
from nereus.config import FusionConfig
from nereus.enums import AnomalyType
from nereus.gating import confidence_gate, size_gate
from nereus.models.ais_message import AisMessage
from nereus.models.anomaly import Anomaly
from nereus.models.detection import Detection
from nereus.models.match_result import MatchResult
from nereus.tracker import AnomalyTracker


class NereusEngine:
    """Fuse one frame of detections against AIS and emit typed anomalies."""

    def __init__(self, config: FusionConfig | None = None) -> None:
        self._config = config or FusionConfig()
        self._tracker = AnomalyTracker(self._config)

    def process_frame(self, detections, ais_messages, frame_ts):
        match = associate(detections, ais_messages, frame_ts, self._config)
        candidates = self._survivors(match)
        self._tracker.update({subject_id for subject_id, *_ in candidates})

        anomalies = []
        for subject_id, anomaly_type, lat, lon, fp_trace in candidates:
            state, count, persistence = self._tracker.assess(subject_id)
            anomalies.append(
                Anomaly(anomaly_type, state, frame_ts, lat, lon, subject_id, count, (*fp_trace, persistence))
            )
        return anomalies

    def _survivors(self, match: MatchResult):
        candidates = []
        for det in match.unmatched_detections:
            size = size_gate(det, self._config)
            confidence = confidence_gate(det, self._config)
            if size.passed and confidence.passed:
                candidates.append((det.det_id, AnomalyType.DARK_VESSEL, det.lat, det.lon, (size, confidence)))
        for ais in match.unmatched_ais:
            candidates.append((str(ais.mmsi), AnomalyType.AIS_GHOST, ais.lat, ais.lon, ()))
        for pair in match.matched:
            if pair.distance_m > self._config.mismatch_dist_m:
                confidence = confidence_gate(pair.detection, self._config)
                if confidence.passed:
                    candidates.append((pair.detection.det_id, AnomalyType.POSITION_MISMATCH, pair.detection.lat, pair.detection.lon, (confidence,)))
        return candidates

from nereus.associate import associate
from nereus.config import FusionConfig
from nereus.enums import AnomalyType
from nereus.gating import confidence_gate, size_gate
from nereus.geo import haversine_m
from nereus.ingest import clean_ais, clean_detections, projected_position
from nereus.models.ais_message import AisMessage
from nereus.models.anomaly import Anomaly
from nereus.models.camera import Camera
from nereus.models.detection import Detection
from nereus.models.match_result import MatchResult
from nereus.tracker import AnomalyTracker


class NereusEngine:
    """Fuse one frame of detections against AIS and emit typed anomalies."""

    def __init__(self, config: FusionConfig | None = None, cameras: list[Camera] | None = None) -> None:
        self._config = config or FusionConfig()
        self._cameras = tuple(cameras or ())
        self._tracker = AnomalyTracker(self._config)

    def process_frame(self, detections, ais_messages, frame_ts):
        detections = clean_detections(detections)
        ais_messages = clean_ais(ais_messages, frame_ts, self._config)
        projected = {a.mmsi: projected_position(a, frame_ts, self._config) for a in ais_messages}

        match = associate(detections, ais_messages, frame_ts, self._config)
        candidates = self._survivors(match, projected)
        self._tracker.update({subject_id for subject_id, *_ in candidates})

        anomalies = []
        for subject_id, anomaly_type, lat, lon, fp_trace in candidates:
            state, count, persistence = self._tracker.assess(subject_id)
            anomalies.append(
                Anomaly(anomaly_type, state, frame_ts, lat, lon, subject_id, count, (*fp_trace, persistence))
            )
        return anomalies

    def _survivors(self, match: MatchResult, projected):
        candidates = []
        for det in match.unmatched_detections:
            size = size_gate(det, self._config)
            confidence = confidence_gate(det, self._config)
            if size.passed and confidence.passed:
                candidates.append((det.det_id, AnomalyType.DARK_VESSEL, det.lat, det.lon, (size, confidence)))
        for ais in match.unmatched_ais:
            lat, lon = projected[ais.mmsi]
            if self._in_coverage(lat, lon):
                candidates.append((str(ais.mmsi), AnomalyType.AIS_GHOST, lat, lon, ()))
        for pair in match.matched:
            if pair.distance_m > self._config.mismatch_dist_m:
                confidence = confidence_gate(pair.detection, self._config)
                if confidence.passed:
                    candidates.append((pair.detection.det_id, AnomalyType.POSITION_MISMATCH, pair.detection.lat, pair.detection.lon, (confidence,)))
        return candidates

    def _in_coverage(self, lat: float, lon: float) -> bool:
        if not self._cameras:
            return False
        return any(haversine_m(lat, lon, cam.lat, cam.lon) <= cam.range_m for cam in self._cameras)

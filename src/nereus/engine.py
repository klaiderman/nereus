import math
from typing import NamedTuple

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
from nereus.models.gate_result import GateResult
from nereus.models.match_result import MatchResult
from nereus.models.matched_pair import MatchedPair
from nereus.tracker import AnomalyTracker


class _Candidate(NamedTuple):
    track_key: tuple
    subject_id: str
    anomaly_type: AnomalyType
    lat: float
    lon: float
    fp_trace: tuple[GateResult, ...]


class NereusEngine:
    """Fuse one frame of detections against AIS and emit typed, traced anomalies.

    Two layers: a stateless association pass whose three outcomes are the three anomaly
    classes, and a stateful persistence tracker, with the false-positive gates between
    them. Each anomaly's `trace` records the gates it cleared.

    `cameras` is the coverage model: an AIS ghost is only raised where a camera should
    have seen the vessel, and with no cameras ghosts are not raised at all.
    """

    def __init__(
        self,
        config: FusionConfig | None = None,
        cameras: list[Camera] | None = None,
    ) -> None:
        self._config = config or FusionConfig()
        self._cameras = tuple(cameras or ())
        self._tracker = AnomalyTracker(self._config)
        self._last_frame_ts: float | None = None

    def process_frame(
        self,
        detections: list[Detection],
        ais_messages: list[AisMessage],
        frame_ts: float,
    ) -> list[Anomaly]:
        # A non-finite frame timestamp is garbage: drop it rather than let a NaN poison
        # the idempotence guard.
        if not math.isfinite(frame_ts):
            return []
        # Idempotence: a replayed or out-of-order frame (at-least-once delivery) must not
        # advance persistence, or one physical moment counts as several confirmations.
        if self._last_frame_ts is not None and frame_ts <= self._last_frame_ts:
            return []
        self._last_frame_ts = frame_ts

        detections = clean_detections(detections)
        ais_messages = clean_ais(ais_messages, frame_ts, self._config)
        projected = {a.mmsi: projected_position(a, frame_ts, self._config) for a in ais_messages}

        match = associate(detections, ais_messages, frame_ts, self._config)
        candidates = self._survivors(match, ais_messages, projected)

        self._tracker.update({candidate.track_key for candidate in candidates})

        anomalies: list[Anomaly] = []
        for candidate in candidates:
            state, count, persistence = self._tracker.assess(candidate.track_key)
            anomalies.append(
                Anomaly(
                    type=candidate.anomaly_type,
                    state=state,
                    timestamp=frame_ts,
                    lat=candidate.lat,
                    lon=candidate.lon,
                    subject_id=candidate.subject_id,
                    confirmations=count,
                    trace=(*candidate.fp_trace, persistence),
                )
            )
        return anomalies

    def _survivors(
        self,
        match: MatchResult,
        ais_messages: list[AisMessage],
        projected: dict[int, tuple[float, float]],
    ) -> list[_Candidate]:
        """Candidates that cleared false-positive gating, before persistence.

        Gating is per type: dark answers to size and confidence, mismatch to confidence,
        ghost to a coverage check. The persistence key is namespaced by origin and type
        so a det_id cannot collide with a str(mmsi).
        """
        candidates: list[_Candidate] = []

        for det in match.unmatched_detections:
            size = size_gate(det, self._config)
            confidence = confidence_gate(det, self._config)
            if size.passed and confidence.passed:
                key = _det_key(det, AnomalyType.DARK_VESSEL)
                candidates.append(
                    _Candidate(key, det.det_id, AnomalyType.DARK_VESSEL, det.lat, det.lon, (size, confidence))
                )

        for ais in match.unmatched_ais:
            lat, lon = projected[ais.mmsi]
            if self._in_coverage(lat, lon):
                key = _mmsi_key(ais.mmsi, AnomalyType.AIS_GHOST)
                candidates.append(_Candidate(key, str(ais.mmsi), AnomalyType.AIS_GHOST, lat, lon, ()))

        for pair in match.matched:
            if self._is_mismatch(pair, ais_messages, projected):
                confidence = confidence_gate(pair.detection, self._config)
                if confidence.passed:
                    key = _det_key(pair.detection, AnomalyType.POSITION_MISMATCH)
                    candidates.append(
                        _Candidate(
                            key,
                            pair.detection.det_id,
                            AnomalyType.POSITION_MISMATCH,
                            pair.detection.lat,
                            pair.detection.lon,
                            (confidence,),
                        )
                    )

        return candidates

    def _in_coverage(self, lat: float, lon: float) -> bool:
        if not self._cameras:
            return False
        return any(
            haversine_m(lat, lon, cam.lat, cam.lon) <= cam.range_m for cam in self._cameras
        )

    def _is_mismatch(
        self,
        pair: MatchedPair,
        ais_messages: list[AisMessage],
        projected: dict[int, tuple[float, float]],
    ) -> bool:
        # Slack for how far the matched AIS was dead-reckoned: an old, fast report
        # explains a position gap without spoofing.
        reckoned_m = haversine_m(pair.ais.lat, pair.ais.lon, *projected[pair.ais.mmsi])
        threshold = self._config.mismatch_dist_m + self._config.mismatch_uncertainty_k * reckoned_m
        if pair.distance_m <= threshold:
            return False
        # Only a real mismatch if no other AIS is within the mismatch distance of the
        # detection. A nearer track means the assignment was wrong, not the position.
        nearest_m = min(
            haversine_m(pair.detection.lat, pair.detection.lon, *projected[ais.mmsi])
            for ais in ais_messages
        )
        return nearest_m > self._config.mismatch_dist_m


def _det_key(det: Detection, anomaly_type: AnomalyType) -> tuple:
    # Tuple keys, not a delimited string, so an id that contains the separator can't
    # collapse two subjects into one persistence count.
    return ("det", det.camera_id, det.det_id, anomaly_type)


def _mmsi_key(mmsi: int, anomaly_type: AnomalyType) -> tuple:
    return ("mmsi", mmsi, anomaly_type)

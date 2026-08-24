from collections.abc import Hashable

from nereus.config import FusionConfig
from nereus.enums import AnomalyState, Gate
from nereus.models.gate_result import GateResult
from nereus.models.track_state import TrackState


class AnomalyTracker:
    """Promotes a candidate to ALERT once it has recurred for `persist_frames` frames.

    Until then it is PENDING. A track survives up to `miss_tolerance` unseen frames with
    its count held, so a dropped frame or brief occlusion doesn't reset progress; a
    longer gap forgets it.
    """

    def __init__(self, config: FusionConfig) -> None:
        self._config = config
        self._states: dict[Hashable, TrackState] = {}

    def update(self, active_ids: set[Hashable]) -> None:
        next_states: dict[Hashable, TrackState] = {}

        for subject_id, state in self._states.items():
            if subject_id in active_ids:
                continue
            misses = state.misses + 1
            if misses <= self._config.miss_tolerance:
                next_states[subject_id] = TrackState(count=state.count, misses=misses)

        for subject_id in active_ids:
            previous = self._states.get(subject_id)
            count = (previous.count if previous else 0) + 1
            next_states[subject_id] = TrackState(count=count, misses=0)

        self._states = next_states

    def assess(self, subject_id: Hashable) -> tuple[AnomalyState, int, GateResult]:
        state = self._states.get(subject_id)
        count = state.count if state else 0
        passed = count >= self._config.persist_frames
        anomaly_state = AnomalyState.ALERT if passed else AnomalyState.PENDING
        detail = f"persisted {count}/{self._config.persist_frames} frames"
        return anomaly_state, count, GateResult(Gate.PERSISTENCE, passed, detail)

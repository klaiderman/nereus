from nereus.config import FusionConfig
from nereus.enums import AnomalyState, Gate
from nereus.models.gate_result import GateResult


class AnomalyTracker:
    """Counts consecutive frames a candidate is seen and promotes it to ALERT."""

    def __init__(self, config: FusionConfig) -> None:
        self._config = config
        self._counts: dict[str, int] = {}

    def update(self, active_ids: set[str]) -> None:
        self._counts = {
            subject_id: self._counts.get(subject_id, 0) + 1 for subject_id in active_ids
        }

    def assess(self, subject_id: str):
        count = self._counts.get(subject_id, 0)
        passed = count >= self._config.persist_frames
        state = AnomalyState.ALERT if passed else AnomalyState.PENDING
        detail = f"persisted {count}/{self._config.persist_frames} frames"
        return state, count, GateResult(Gate.PERSISTENCE, passed, detail)

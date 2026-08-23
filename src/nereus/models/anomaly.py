from dataclasses import dataclass

from nereus.enums import AnomalyState, AnomalyType
from nereus.models.gate_result import GateResult


@dataclass(frozen=True, slots=True)
class Anomaly:
    """A typed anomaly plus the full trace of gates it cleared to reach its state."""

    type: AnomalyType
    state: AnomalyState
    timestamp: float
    lat: float
    lon: float
    subject_id: str
    confirmations: int
    trace: tuple[GateResult, ...]

from dataclasses import dataclass

from nereus.enums import Gate


@dataclass(frozen=True, slots=True)
class GateResult:
    """One line of an anomaly's audit trail: which gate ran, and what it decided."""

    gate: Gate
    passed: bool
    detail: str

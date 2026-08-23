from nereus.config import FusionConfig
from nereus.enums import Gate
from nereus.models.detection import Detection
from nereus.models.gate_result import GateResult


def size_gate(detection: Detection, config: FusionConfig) -> GateResult:
    """Vessels below the exempt length carry no AIS obligation."""
    passed = detection.length_m >= config.exempt_length_m
    detail = (
        f"length {detection.length_m:.0f}m "
        f"{'>=' if passed else '<'} exempt {config.exempt_length_m:.0f}m"
    )
    return GateResult(Gate.SIZE, passed, detail)


def confidence_gate(detection: Detection, config: FusionConfig) -> GateResult:
    """Low-confidence detections are suppressed before they can alert."""
    passed = detection.confidence >= config.min_confidence
    detail = (
        f"confidence {detection.confidence:.2f} "
        f"{'>=' if passed else '<'} min {config.min_confidence:.2f}"
    )
    return GateResult(Gate.CONFIDENCE, passed, detail)

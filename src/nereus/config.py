from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FusionConfig:
    """Thresholds for the fusion pipeline."""

    gate_radius_m: float = 200.0
    mismatch_dist_m: float = 100.0
    persist_frames: int = 3
    exempt_length_m: float = 20.0
    min_confidence: float = 0.5

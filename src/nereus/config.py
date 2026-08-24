from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FusionConfig:
    """Pipeline thresholds, validated on construction so a bad value (e.g.
    persist_frames=0) fails at the boundary rather than downstream."""

    gate_radius_m: float = 200.0
    """Max detection-to-AIS distance to consider the two the same vessel."""

    mismatch_dist_m: float = 100.0
    """A matched pair separated by more than this (plus projection slack) is a mismatch."""

    persist_frames: int = 3
    """Consecutive confirmations a candidate needs before it becomes an alert."""

    miss_tolerance: int = 2
    """Unseen frames a candidate may survive — a dropped frame or brief occlusion —
    before it is forgotten and its count restarts."""

    exempt_length_m: float = 20.0
    """Vessels shorter than this carry no AIS obligation (proxy for SOLAS V/19 / 300 GT).

    Length stands in for gross tonnage; they correlate but aren't equal, so this is a
    conservative operational default rather than a legal threshold.
    """

    min_confidence: float = 0.5
    """Detections scored below this are treated as unreliable and never alert."""

    max_ais_age_s: float = 180.0
    """AIS reports older than this (relative to the frame) are dropped before fusion; a
    stale report projected over minutes drifts too far to trust."""

    max_plausible_sog_kn: float = 80.0
    """At or above this speed a report is treated as an AIS 'not available' sentinel
    (102.3 kn) or garbage: its raw position is used, it is not dead-reckoned."""

    mismatch_uncertainty_k: float = 1.0
    """Slack added to the mismatch threshold per metre of dead-reckoning: the older and
    faster the AIS report, the more a position gap is projection, not spoofing."""

    def __post_init__(self) -> None:
        if self.persist_frames < 1:
            raise ValueError("persist_frames must be >= 1")
        if self.miss_tolerance < 0:
            raise ValueError("miss_tolerance must be >= 0")
        if not 0.0 < self.mismatch_dist_m <= self.gate_radius_m:
            raise ValueError("require 0 < mismatch_dist_m <= gate_radius_m")
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be in [0, 1]")
        # Positive form so NaN (which fails every comparison) is rejected, not accepted.
        if not self.exempt_length_m > 0.0:
            raise ValueError("exempt_length_m must be > 0")
        if not self.max_ais_age_s > 0.0:
            raise ValueError("max_ais_age_s must be > 0")
        if not self.max_plausible_sog_kn > 0.0:
            raise ValueError("max_plausible_sog_kn must be > 0")
        if not self.mismatch_uncertainty_k >= 0.0:
            raise ValueError("mismatch_uncertainty_k must be >= 0")

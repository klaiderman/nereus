from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TrackState:
    """Per-subject persistence bookkeeping: consecutive confirmations, and current gap."""

    count: int
    misses: int

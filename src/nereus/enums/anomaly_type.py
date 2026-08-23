from enum import StrEnum, auto


class AnomalyType(StrEnum):
    DARK_VESSEL = auto()
    AIS_GHOST = auto()
    POSITION_MISMATCH = auto()
    SPOOF_SUSPECT = auto()

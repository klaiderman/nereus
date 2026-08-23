from enum import StrEnum, auto


class AnomalyState(StrEnum):
    PENDING = auto()
    ALERT = auto()

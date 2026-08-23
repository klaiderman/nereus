from enum import StrEnum, auto


class VesselClass(StrEnum):
    FISHING = auto()
    CARGO = auto()
    TANKER = auto()
    PASSENGER = auto()
    SMALL_CRAFT = auto()
    UNKNOWN = auto()

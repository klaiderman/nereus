import math

from nereus.config import FusionConfig
from nereus.geo import dead_reckon
from nereus.models.ais_message import AisMessage
from nereus.models.detection import Detection

_COG_NOT_AVAILABLE = 360.0


def clean_detections(detections: list[Detection]) -> list[Detection]:
    """Drop detections with non-finite or out-of-range geometry, so one bad upstream
    record never crashes the frame or corrupts the cost matrix."""
    return [
        det
        for det in detections
        if _valid_lat_lon(det.lat, det.lon) and _finite(det.length_m, det.confidence)
    ]


def clean_ais(
    ais_messages: list[AisMessage], frame_ts: float, config: FusionConfig
) -> list[AisMessage]:
    """Validate, drop-if-stale, and deduplicate AIS to one report per vessel per frame.

    Class-A transponders repeat every 2-10 s, so any batch holds several reports per
    MMSI; without collapsing them the extras surface as ghosts. We keep the report whose
    timestamp is closest to the frame time."""
    kept: dict[int, AisMessage] = {}
    for ais in ais_messages:
        if not _valid_lat_lon(ais.lat, ais.lon):
            continue
        if not _valid_mmsi(ais.mmsi):
            continue
        if not _finite(ais.sog, ais.cog, ais.timestamp):
            continue
        if frame_ts - ais.timestamp > config.max_ais_age_s:
            continue
        current = kept.get(ais.mmsi)
        if current is None or _closer(ais, current, frame_ts):
            kept[ais.mmsi] = ais
    return list(kept.values())


def projected_position(
    ais: AisMessage, frame_ts: float, config: FusionConfig
) -> tuple[float, float]:
    """Dead-reckon an AIS report to the frame time, unless its SOG/COG read as the ITU-R
    'not available' sentinels (or implausible garbage), in which case its raw position is
    used instead."""
    if not 0.0 <= ais.sog < config.max_plausible_sog_kn or not 0.0 <= ais.cog < _COG_NOT_AVAILABLE:
        return ais.lat, ais.lon
    return dead_reckon(ais.lat, ais.lon, ais.sog, ais.cog, frame_ts - ais.timestamp)


def _finite(*values: float) -> bool:
    return all(math.isfinite(v) for v in values)


def _valid_lat_lon(lat: float, lon: float) -> bool:
    return _finite(lat, lon) and -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0


def _valid_mmsi(mmsi: int) -> bool:
    return 100_000_000 <= mmsi <= 999_999_999


def _closer(candidate: AisMessage, current: AisMessage, frame_ts: float) -> bool:
    return abs(frame_ts - candidate.timestamp) < abs(frame_ts - current.timestamp)

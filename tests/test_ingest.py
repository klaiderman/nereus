from nereus.config import FusionConfig
from nereus.enums import SensorType, VesselClass
from nereus.ingest import clean_ais, clean_detections, projected_position
from nereus.models.ais_message import AisMessage
from nereus.models.detection import Detection

_CONFIG = FusionConfig()


def _det(lat, lon, length=100.0, confidence=0.9, ts=0.0):
    return Detection(ts, "d", "cam-1", lat, lon, VesselClass.CARGO, length, 0.0, confidence, SensorType.EO)


def _ais(mmsi, lat=31.8, lon=34.6, ts=0.0, sog=0.0, cog=0.0):
    return AisMessage(ts, mmsi, lat, lon, sog, cog, 70, 100.0)


def test_clean_detections_drops_non_finite_and_out_of_range():
    good = _det(31.8, 34.6)
    assert clean_detections([good, _det(float("nan"), 34.6), _det(200.0, 34.6)]) == [good]


def test_clean_detections_drops_nan_fields():
    assert clean_detections([_det(31.8, 34.6, length=float("nan"))]) == []
    assert clean_detections([_det(31.8, 34.6, confidence=float("nan"))]) == []


def test_clean_ais_rejects_invalid_mmsi():
    assert clean_ais([_ais(0)], 0.0, _CONFIG) == []
    assert clean_ais([_ais(123)], 0.0, _CONFIG) == []  # too short
    assert len(clean_ais([_ais(123456789)], 0.0, _CONFIG)) == 1


def test_clean_ais_drops_stale_reports():
    kept = clean_ais([_ais(123456789, ts=0.0), _ais(987654321, ts=-1000.0)], 0.0, _CONFIG)
    assert [a.mmsi for a in kept] == [123456789]


def test_clean_ais_dedups_by_mmsi_keeping_nearest_time():
    kept = clean_ais([_ais(123456789, ts=2.0), _ais(123456789, ts=9.0)], 10.0, _CONFIG)
    assert len(kept) == 1
    assert kept[0].timestamp == 9.0


def test_projected_position_uses_raw_for_sentinel_speed():
    sentinel = _ais(123456789, lat=31.8, lon=34.6, ts=0.0, sog=102.3, cog=90.0)
    assert projected_position(sentinel, 60.0, _CONFIG) == (31.8, 34.6)


def test_projected_position_uses_raw_for_negative_speed():
    garbage = _ais(123456789, lat=31.8, lon=34.6, ts=0.0, sog=-5.0, cog=90.0)
    assert projected_position(garbage, 60.0, _CONFIG) == (31.8, 34.6)


def test_clean_ais_drops_nan_timestamp_without_evicting_the_valid_report():
    good = _ais(123456789, ts=0.0)
    nan_first = _ais(123456789, ts=float("nan"))
    kept = clean_ais([nan_first, good], 0.0, _CONFIG)
    assert kept == [good]

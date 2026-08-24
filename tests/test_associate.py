from nereus.associate import associate
from nereus.config import FusionConfig
from nereus.enums import SensorType, VesselClass
from nereus.models.ais_message import AisMessage
from nereus.models.detection import Detection

_CONFIG = FusionConfig()


def _detection(lat, lon, ts=0.0):
    return Detection(ts, "d", "cam-1", lat, lon, VesselClass.CARGO, 100.0, 0.0, 0.9, SensorType.EO)


def _ais(lat, lon, ts=0.0, sog=0.0, cog=0.0):
    return AisMessage(ts, 1, lat, lon, sog, cog, 70, 100.0)


def test_colocated_detection_and_ais_match():
    result = associate([_detection(31.80, 34.60)], [_ais(31.80, 34.60)], 0.0, _CONFIG)
    assert len(result.matched) == 1
    assert not result.unmatched_detections
    assert not result.unmatched_ais


def test_distant_detection_and_ais_do_not_match():
    result = associate([_detection(31.80, 34.60)], [_ais(31.90, 34.70)], 0.0, _CONFIG)
    assert not result.matched
    assert len(result.unmatched_detections) == 1
    assert len(result.unmatched_ais) == 1


def test_stale_ais_is_projected_into_the_gate():
    # AIS is 60 s old and 300 m south, steaming due north at 9.72 kn (~300 m in 60 s).
    # Raw, it is out of gate; projected to frame time, it lands on the detection.
    detection = _detection(31.80000, 34.60000, ts=60.0)
    stale_ais = _ais(31.79730, 34.60000, ts=0.0, sog=9.72, cog=0.0)
    result = associate([detection], [stale_ais], 60.0, _CONFIG)
    assert len(result.matched) == 1


def test_empty_inputs_partition_cleanly():
    result = associate([_detection(31.8, 34.6)], [], 0.0, _CONFIG)
    assert not result.matched
    assert len(result.unmatched_detections) == 1
    assert not result.unmatched_ais

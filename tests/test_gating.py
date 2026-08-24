from nereus.config import FusionConfig
from nereus.enums import Gate, SensorType, VesselClass
from nereus.gating import confidence_gate, size_gate
from nereus.models.detection import Detection

_CONFIG = FusionConfig()


def _detection(length_m, confidence):
    return Detection(
        timestamp=0.0,
        det_id="d",
        camera_id="cam-1",
        lat=31.8,
        lon=34.6,
        vessel_class=VesselClass.UNKNOWN,
        length_m=length_m,
        heading=0.0,
        confidence=confidence,
        sensor=SensorType.EO,
    )


def test_small_craft_is_size_exempt():
    result = size_gate(_detection(length_m=8.0, confidence=0.9), _CONFIG)
    assert result.gate is Gate.SIZE
    assert result.passed is False


def test_large_vessel_clears_size_gate():
    assert size_gate(_detection(length_m=120.0, confidence=0.9), _CONFIG).passed is True


def test_low_confidence_detection_is_suppressed():
    assert confidence_gate(_detection(length_m=120.0, confidence=0.3), _CONFIG).passed is False


def test_confident_detection_clears_gate():
    assert confidence_gate(_detection(length_m=120.0, confidence=0.9), _CONFIG).passed is True

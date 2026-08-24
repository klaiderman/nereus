import pytest

from nereus.models.camera import Camera


def test_valid_camera_constructs():
    Camera("cam-1", 31.8, 34.6, 3000.0)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"range_m": -1.0},
        {"range_m": 0.0},
        {"range_m": float("nan")},
        {"lat": 91.0},
        {"lat": float("nan")},
        {"lon": 181.0},
    ],
)
def test_invalid_camera_raises(kwargs):
    fields = {"camera_id": "c", "lat": 31.8, "lon": 34.6, "range_m": 3000.0}
    fields.update(kwargs)
    with pytest.raises(ValueError):
        Camera(**fields)

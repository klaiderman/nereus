import pytest

from nereus.config import FusionConfig


def test_defaults_are_valid():
    FusionConfig()  # must not raise


@pytest.mark.parametrize(
    "kwargs",
    [
        {"persist_frames": 0},
        {"miss_tolerance": -1},
        {"mismatch_dist_m": 300.0},  # > gate_radius_m default (200)
        {"mismatch_dist_m": 0.0},
        {"min_confidence": 1.5},
        {"min_confidence": -0.1},
        {"exempt_length_m": 0.0},
        {"max_ais_age_s": 0.0},
        {"max_plausible_sog_kn": 0.0},
        {"mismatch_uncertainty_k": -1.0},
        {"exempt_length_m": float("nan")},
        {"max_ais_age_s": float("nan")},
        {"max_plausible_sog_kn": float("nan")},
        {"mismatch_uncertainty_k": float("nan")},
        {"mismatch_dist_m": float("nan")},
        {"min_confidence": float("nan")},
    ],
)
def test_invalid_config_raises(kwargs):
    with pytest.raises(ValueError):
        FusionConfig(**kwargs)

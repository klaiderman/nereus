from nereus import NereusEngine
from nereus.enums import AnomalyState, AnomalyType, Gate, SensorType, VesselClass
from nereus.models.ais_message import AisMessage
from nereus.models.camera import Camera
from nereus.models.detection import Detection

from scenario import harbour_camera, harbour_frame

_M = 1.0 / 111_194.9  # ~one metre in degrees of latitude


def _by_id(anomalies):
    return {anomaly.subject_id: anomaly for anomaly in anomalies}


def _det(det_id, lat, lon, *, camera_id="cam-1", length=100.0, confidence=0.9, ts=0.0):
    return Detection(ts, det_id, camera_id, lat, lon, VesselClass.CARGO, length, 0.0, confidence, SensorType.EO)


def _ais(mmsi, lat, lon, *, ts=0.0, sog=0.0, cog=0.0):
    return AisMessage(ts, mmsi, lat, lon, sog, cog, 70, 100.0)


# The harbour regression scenario

def test_exempt_skiff_is_never_alerted():
    engine = NereusEngine(cameras=harbour_camera())
    for ts in range(5):
        assert "skiff" not in _by_id(engine.process_frame(*harbour_frame(float(ts))))


def test_dark_vessel_earns_its_alert_after_persistence():
    engine = NereusEngine(cameras=harbour_camera())
    states = []
    dark = None
    for ts in range(3):
        dark = _by_id(engine.process_frame(*harbour_frame(float(ts))))["dark"]
        states.append(dark.state)
    assert states == [AnomalyState.PENDING, AnomalyState.PENDING, AnomalyState.ALERT]
    assert dark.type is AnomalyType.DARK_VESSEL
    assert dark.confirmations == 3
    assert {gate.gate: gate.passed for gate in dark.trace} == {
        Gate.SIZE: True,
        Gate.CONFIDENCE: True,
        Gate.PERSISTENCE: True,
    }


def test_ghost_is_raised_from_unmatched_ais_in_coverage():
    engine = NereusEngine(cameras=harbour_camera())
    anomalies = {}
    for ts in range(3):
        anomalies = _by_id(engine.process_frame(*harbour_frame(float(ts))))
    ghost = anomalies["111111111"]
    assert ghost.type is AnomalyType.AIS_GHOST
    assert ghost.state is AnomalyState.ALERT


def test_clean_pair_raises_nothing():
    engine = NereusEngine(cameras=harbour_camera())
    anomalies = _by_id(engine.process_frame(*harbour_frame(0.0)))
    assert "clean" not in anomalies
    assert "222222222" not in anomalies


# N-01: ghosts require a coverage model

def test_ghost_is_not_raised_without_coverage():
    engine = NereusEngine()  # no cameras
    anomalies = {}
    for ts in range(3):
        anomalies = _by_id(engine.process_frame(*harbour_frame(float(ts))))
    assert "111111111" not in anomalies


# N-02: one bad record must not take down the frame

def test_nan_detection_does_not_crash_the_frame():
    engine = NereusEngine()
    dark = _det("dark", 31.810, 34.610, length=120.0)
    junk = _det("junk", float("nan"), 34.610)
    anomalies = None
    for ts in range(3):
        anomalies = _by_id(engine.process_frame([dark, junk], [], float(ts)))
    assert anomalies["dark"].type is AnomalyType.DARK_VESSEL
    assert anomalies["dark"].state is AnomalyState.ALERT


# N-03: duplicate AIS for one vessel must not manufacture a ghost

def test_duplicate_mmsi_does_not_manufacture_a_ghost():
    engine = NereusEngine(cameras=harbour_camera())
    anomalies = None
    for ts in range(3):
        anomalies = engine.process_frame([_det("v", 31.810, 34.610, ts=float(ts))],
                                         [_ais(123456789, 31.810, 34.610, ts=float(ts)),
                                          _ais(123456789, 31.810, 34.610, ts=float(ts))],
                                         float(ts))
    assert anomalies == []


# N-04: a closer AIS explains the gap; no false mismatch

def test_no_false_mismatch_when_a_closer_ais_exists():
    engine = NereusEngine()
    anomalies = None
    for ts in range(3):
        d1 = _det("d1", 31.8000, 34.6000, ts=float(ts))
        d2 = _det("d2", 31.8000 + 100 * _M, 34.6000, ts=float(ts))  # 100 m north
        a1 = _ais(111111111, 31.8000 + 50 * _M, 34.6000, ts=float(ts))  # 50 m N of d1
        a2 = _ais(222222222, 31.8000 - 150 * _M, 34.6000, ts=float(ts))  # 150 m S of d1
        anomalies = engine.process_frame([d1, d2], [a1, a2], float(ts))
    assert all(a.type is not AnomalyType.POSITION_MISMATCH for a in anomalies)


# N-05: a subject that flips type must not inherit the other type's count

def test_type_flip_does_not_inherit_count():
    engine = NereusEngine()
    # Frames 0-1: "v" is a POSITION_MISMATCH (matched AIS 150 m off, nothing closer).
    for ts in range(2):
        det = _det("v", 31.8000, 34.6000, ts=float(ts))
        ais = _ais(111111111, 31.8000 + 150 * _M, 34.6000, ts=float(ts))
        engine.process_frame([det], [ais], float(ts))
    # Frame 2: the AIS drops -> "v" is now a DARK_VESSEL, starting a fresh count.
    dark = _by_id(engine.process_frame([_det("v", 31.8000, 34.6000, ts=2.0)], [], 2.0))["v"]
    assert dark.type is AnomalyType.DARK_VESSEL
    assert dark.confirmations == 1
    assert dark.state is AnomalyState.PENDING


# N-06: det_id and str(mmsi) live in separate namespaces

def test_det_id_and_mmsi_do_not_collide():
    engine = NereusEngine(cameras=harbour_camera())
    # Frames 0-1: a ghost with mmsi 555555555 climbs to count 2.
    for ts in range(2):
        engine.process_frame([], [_ais(555555555, 31.815, 34.615, ts=float(ts))], float(ts))
    # Frame 2: a detection whose det_id is "555555555" must start fresh, not inherit.
    dark = _by_id(engine.process_frame([_det("555555555", 31.810, 34.610, ts=2.0)], [], 2.0))["555555555"]
    assert dark.type is AnomalyType.DARK_VESSEL
    assert dark.confirmations == 1


# N-07: a replayed / stale frame must not advance persistence

def test_frame_replay_is_idempotent():
    engine = NereusEngine(cameras=harbour_camera())
    first = engine.process_frame(*harbour_frame(0.0))
    replay = engine.process_frame(*harbour_frame(0.0))  # same ts
    assert replay == []
    assert _by_id(first)["dark"].confirmations == 1


# N-10: an AIS 'not available' SOG sentinel must not push the track out of gate

def test_sentinel_sog_still_matches():
    engine = NereusEngine()
    anomalies = None
    for ts in range(3):
        anomalies = engine.process_frame([_det("v", 31.810, 34.610, ts=float(ts))],
                                         [_ais(123456789, 31.810, 34.610, ts=float(ts), sog=102.3, cog=90.0)],
                                         float(ts))
    assert anomalies == []


# N-12: the same det_id from two cameras is two vessels

def test_cross_camera_det_id_stays_independent():
    engine = NereusEngine()
    anomalies = engine.process_frame(
        [_det("1", 31.810, 34.610, camera_id="A"), _det("1", 31.900, 34.700, camera_id="B")],
        [],
        0.0,
    )
    assert len(anomalies) == 2
    assert all(a.confirmations == 1 for a in anomalies)


# N-13: candidacy must not depend on input ordering

def test_nan_frame_ts_is_dropped_and_does_not_poison_the_guard():
    engine = NereusEngine()
    assert engine.process_frame([_det("dark", 31.810, 34.610)], [], float("nan")) == []
    dark = None
    for ts in range(3):
        dark = _by_id(engine.process_frame([_det("dark", 31.810, 34.610, ts=float(ts))], [], float(ts)))["dark"]
    assert dark.state is AnomalyState.ALERT


def test_ids_containing_the_delimiter_do_not_collide():
    engine = NereusEngine()
    anomalies = engine.process_frame(
        [_det("c", 31.810, 34.610, camera_id="a:b"), _det("b:c", 31.900, 34.700, camera_id="a")],
        [],
        0.0,
    )
    assert len(anomalies) == 2
    assert all(anomaly.confirmations == 1 for anomaly in anomalies)


def test_association_is_order_independent():
    engine_a = NereusEngine()
    engine_b = NereusEngine()
    d1 = _det("d1", 31.810, 34.610)
    d2 = _det("d2", 31.810, 34.610)  # co-located rivals for one behaviour
    a = engine_a.process_frame([d1, d2], [], 0.0)
    b = engine_b.process_frame([d2, d1], [], 0.0)
    assert {x.subject_id for x in a} == {x.subject_id for x in b}

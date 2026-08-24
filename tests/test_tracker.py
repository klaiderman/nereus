from nereus.config import FusionConfig
from nereus.enums import AnomalyState, Gate
from nereus.tracker import AnomalyTracker


def test_candidate_is_pending_until_it_persists():
    tracker = AnomalyTracker(FusionConfig(persist_frames=3))
    states = []
    for _ in range(3):
        tracker.update({"v"})
        state, _count, _gate = tracker.assess("v")
        states.append(state)
    assert states == [AnomalyState.PENDING, AnomalyState.PENDING, AnomalyState.ALERT]


def test_persistence_gate_reports_the_count():
    tracker = AnomalyTracker(FusionConfig(persist_frames=3))
    tracker.update({"v"})
    _state, count, gate = tracker.assess("v")
    assert count == 1
    assert gate.gate is Gate.PERSISTENCE
    assert gate.passed is False


def test_a_brief_gap_is_tolerated():
    tracker = AnomalyTracker(FusionConfig(persist_frames=3, miss_tolerance=2))
    tracker.update({"v"})  # 1
    tracker.update({"v"})  # 2
    tracker.update(set())  # gap: unseen once, count held at 2
    tracker.update({"v"})  # seen again -> 3
    state, count, _gate = tracker.assess("v")
    assert count == 3
    assert state is AnomalyState.ALERT


def test_a_gap_longer_than_tolerance_forgets_the_track():
    tracker = AnomalyTracker(FusionConfig(persist_frames=3, miss_tolerance=2))
    tracker.update({"v"})  # 1
    tracker.update({"v"})  # 2
    tracker.update(set())  # miss 1
    tracker.update(set())  # miss 2
    tracker.update(set())  # miss 3 > tolerance -> forgotten
    tracker.update({"v"})  # returns as a fresh track
    _state, count, _gate = tracker.assess("v")
    assert count == 1

from industry_x_ai.metrics import CycleLogger


def test_summary_and_csv(tmp_path):
    L = CycleLogger()
    L.on_world_event({"event": "spawned", "piece": "p1", "color": "red", "shape": "cube", "t": 0})
    L.on_world_event({"event": "ready", "piece": "p1", "t": 5})
    L.on_world_event({"event": "binned", "piece": "p1", "bin": "A", "expected_bin": "A", "correct": True, "t": 25})
    L.on_distance(0.3, 0.08)
    s = L.summary(60)
    assert s["success"] == 1 and s["cycle_mean_s"] == 20 and s["collisions"] == 0
    L.write_csv(str(tmp_path / "a.csv"))
    assert "piece_id" in (tmp_path / "a.csv").read_text()

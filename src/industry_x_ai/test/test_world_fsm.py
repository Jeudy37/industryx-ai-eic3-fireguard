import pytest

from industry_x_ai import config as C
from industry_x_ai.headless_sim import run
from industry_x_ai.world_model import WorldModel


def test_conveyor_queue_and_ready():
    w = WorldModel(3, spawn_period=1.0)
    t, ready = 0.0, []
    while t < 40:
        w.maybe_spawn(t)
        ready += w.step(t, 0.02)
        t += 0.02
    assert len(ready) == 1 and ready[0]["piece"] == "piece_1"       # les autres attendent derrière
    xs = sorted(p.x for p in w.pieces.values())
    assert xs[-1] == pytest.approx(C.STOP_X, abs=1e-6)
    assert all(b - a >= C.QUEUE_SPACING - 1e-6 for a, b in zip(xs, xs[1:]))


def test_nominal_ten_cycles_all_sorted_no_collision():
    log, world, orch, _ = run(10)
    s = log.summary()
    assert s["pieces_processed"] == 10 and s["success"] == 10 and s["errors"] == 0
    assert s["collisions"] == 0 and s["min_arm_distance_m"] > C.WARNING_DIST
    assert set(s["per_bin"]) == {"A", "B", "C"} and all(v > 0 for v in s["per_bin"].values())
    for p in world.pieces.values():
        assert p.bin == C.BIN_RULE[p.color]


def test_random_pieces_sorted_correctly():
    log, *_ = run(12, randomize=True, seed=7)
    assert log.summary()["success"] == 12


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_robustness_grasp_failures_recover_without_collision(seed):
    log, world, orch, _ = run(10, fail_rate=0.25, seed=seed)
    s = log.summary()
    assert s["collisions"] == 0
    assert s["pieces_processed"] == 10                      # aucun blocage (pas de deadlock)
    assert s["errors"] == 0 or all(r["result"] == "ABANDON" for r in log.rows() if r["result"] != "OK")
    assert sum(r["retries"] for r in log.rows()) > 0        # des reprises ont bien eu lieu
    assert orch.lock is None


def test_lock_mutual_exclusion_property():
    """Pendant tout un run, A et B ne sont jamais simultanément en zone de transfert."""
    from industry_x_ai import headless_sim as hs
    from industry_x_ai.robot_controller import ArmController
    seen = {"both": 0}
    orig = ArmController.step

    arms = []

    def spy(self, dt):
        if self not in arms:
            arms.append(self)
        r = orig(self, dt)
        if len(arms) == 2 and all(a.zone() == "TRANSFER" and a.task != "INIT" for a in arms):
            seen["both"] += 1
        return r
    ArmController.step = spy
    try:
        hs.run(6)
    finally:
        ArmController.step = orig
    assert seen["both"] == 0

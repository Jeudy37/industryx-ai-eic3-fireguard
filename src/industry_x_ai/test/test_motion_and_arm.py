import math

from industry_x_ai import config as C
from industry_x_ai.collision import min_arm_distance
from industry_x_ai.kinematics import segments, forward_points
from industry_x_ai.motion import Grip, Move, PlanExecutor, smooth
from industry_x_ai.robot_controller import ArmController


def test_smooth_endpoints():
    assert smooth(0) == 0 and smooth(1) == 1 and abs(smooth(0.5) - 0.5) < 1e-12


def test_executor_reaches_target_and_fires_grip():
    ex = PlanExecutor((0, 0, 0, 0))
    ex.load([Move((1, 0.5, 0.2, 0.1)), Grip(True, "p1")])
    evs = []
    for _ in range(2000):
        evs += ex.step(0.01)
    assert not ex.busy and evs == [{"type": "grip", "closed": True, "piece_id": "p1"}]
    assert max(abs(a - b) for a, b in zip(ex.q, (1, 0.5, 0.2, 0.1))) < 1e-9


def _run_to_idle(arm, limit=60.0, dt=0.02):
    t = 0.0
    while arm.state == "BUSY" and t < limit:
        arm.step(dt)
        t += dt
    return t


def test_arm_init_then_commands_and_rejects_wrong_command():
    a = ArmController("A")
    _run_to_idle(a)
    assert a.state == "IDLE" and a.last_done == 0
    assert not a.submit({"cmd_id": 1, "cmd": "PICK_TRANSFER", "piece_id": "x"})   # commande de B
    assert a.state == "ERROR"
    a.clear_error()
    assert a.submit({"cmd_id": 2, "cmd": "PICK_BELT", "piece_id": "p", "pos": [0, 0, 0.43]})
    assert not a.submit({"cmd_id": 3, "cmd": "HOME"})        # occupé -> refusé


def test_never_below_table_and_zone():
    for role in "AB":
        arm = ArmController(role)
        _run_to_idle(arm)
        cmds = ([{"cmd": "PICK_BELT", "piece_id": "p", "pos": [0, 0, 0.43]}, {"cmd": "PLACE_TRANSFER"}, {"cmd": "HOME"}]
                if role == "A" else
                [{"cmd": "PICK_TRANSFER", "piece_id": "p"}] + [{"cmd": "PLACE_BIN", "bin": b} for b in "ABC"] + [{"cmd": "HOME"}])
        for i, c in enumerate(cmds, 1):
            c["cmd_id"] = i
            assert arm.submit(c)
            while arm.state == "BUSY":
                arm.step(0.02)
                pts = forward_points(C.SPECS[role], arm.q)
                assert all(pts[k][2] >= C.TABLE_TOP_Z + 0.02 for k in ("shoulder", "elbow", "wrist"))
                assert pts["tool"][2] >= C.Z_GRASP - 0.02


def test_all_primitive_pairs_keep_clearance():
    """Toutes les poses de A (hors zone T) combinées à toutes celles de B restent à distance sûre,
    et A/B ne sont jamais ensemble en zone T (verrou) -> pas de collision possible."""
    def poses(role):
        arm = ArmController(role)
        _run_to_idle(arm)
        cmds = ([{"cmd": "PICK_BELT", "piece_id": "p", "pos": [0, 0, 0.43]}, {"cmd": "PLACE_TRANSFER"}, {"cmd": "HOME"}]
                if role == "A" else
                [{"cmd": "PICK_TRANSFER", "piece_id": "p"}] + [{"cmd": "PLACE_BIN", "bin": b} for b in "ABC"] + [{"cmd": "HOME"}])
        out = [(arm.q, arm.zone())]
        for i, c in enumerate(cmds, 1):
            c["cmd_id"] = i
            arm.submit(c)
            while arm.state == "BUSY":
                arm.step(0.05)
                out.append((arm.q, arm.zone()))
        return out
    pa, pb = poses("A"), poses("B")
    worst = 9.0
    for qa, za in pa:
        for qb, zb in pb:
            if za == "TRANSFER" and zb == "TRANSFER":
                continue                         # exclu par le verrou
            worst = min(worst, min_arm_distance(segments(C.ROBOT_A, qa), segments(C.ROBOT_B, qb)))
    assert worst > C.WARNING_DIST, worst

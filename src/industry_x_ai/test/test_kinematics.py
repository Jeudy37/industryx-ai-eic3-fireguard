import math

import pytest

from industry_x_ai import config as C
from industry_x_ai.kinematics import (UnreachableError, forward_tcp, inverse_kinematics)


def _waypoints():
    pts = [("A", C.HOME_TCP["A"]), ("B", C.HOME_TCP["B"])]
    for r in "AB":
        pts += [(r, (*C.TRANSFER_XY, C.Z_HOVER)), (r, (*C.TRANSFER_XY, C.Z_GRASP))]
    pts += [("A", (C.STOP_X, C.BELT_Y, C.Z_HOVER)), ("A", (C.STOP_X, C.BELT_Y, C.Z_GRASP))]
    for b, (x, y) in C.BINS.items():
        pts += [("B", (x, y, C.Z_HOVER)), ("B", (x, y, C.Z_BIN_RELEASE))]
    return pts


@pytest.mark.parametrize("role,p", _waypoints())
def test_ik_fk_roundtrip(role, p):
    q = inverse_kinematics(C.SPECS[role], p)
    t = forward_tcp(C.SPECS[role], q)
    assert all(abs(a - b) < 1e-6 for a, b in zip(t, p))
    # l'outil doit pointer vers le bas
    assert abs((q[1] + q[2] + q[3]) - math.pi) < 1e-6


def test_unreachable():
    with pytest.raises(UnreachableError):
        inverse_kinematics(C.ROBOT_A, (3.0, 3.0, 0.5))
    with pytest.raises(UnreachableError):
        inverse_kinematics(C.ROBOT_A, (0.0, 0.45, 0.5))   # sur l'axe

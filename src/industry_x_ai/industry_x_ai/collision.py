"""Surveillance de distance entre les deux bras (modèle « capsules »).

Chaque segment de bras est une capsule de rayon CAPSULE_RADIUS. Si la distance axe-à-axe
minimale entre un segment de A et un segment de B devient < COLLISION_DIST, les capsules
se touchent : c'est compté comme collision. Utilisé en ligne par le nœud de supervision
et hors ligne par les tests unitaires.
"""
from __future__ import annotations

from typing import Iterable, Tuple

import numpy as np

from .kinematics import Vec3

Segment = Tuple[Vec3, Vec3]


def segment_distance(s1: Segment, s2: Segment) -> float:
    """Distance minimale entre deux segments 3D (Ericson, Real-Time Collision Detection)."""
    p1, q1 = np.array(s1[0], float), np.array(s1[1], float)
    p2, q2 = np.array(s2[0], float), np.array(s2[1], float)
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a, e, f = d1 @ d1, d2 @ d2, d2 @ r
    eps = 1e-12
    if a <= eps and e <= eps:
        return float(np.linalg.norm(r))
    if a <= eps:
        s, t = 0.0, min(max(f / e, 0.0), 1.0)
    else:
        c = d1 @ r
        if e <= eps:
            t, s = 0.0, min(max(-c / a, 0.0), 1.0)
        else:
            b = d1 @ d2
            denom = a * e - b * b
            s = min(max((b * f - c * e) / denom, 0.0), 1.0) if denom > eps else 0.0
            t = (b * s + f) / e
            if t < 0.0:
                t, s = 0.0, min(max(-c / a, 0.0), 1.0)
            elif t > 1.0:
                t, s = 1.0, min(max((b - c) / a, 0.0), 1.0)
    return float(np.linalg.norm((p1 + d1 * s) - (p2 + d2 * t)))


def min_arm_distance(segs_a: Iterable[Segment], segs_b: Iterable[Segment],
                     skip_base_segment: bool = True) -> float:
    """Distance minimale entre tous les segments de A et de B (le socle fixe est ignoré)."""
    la, lb = list(segs_a), list(segs_b)
    if skip_base_segment:
        la, lb = la[1:], lb[1:]
    return min(segment_distance(x, y) for x in la for y in lb)

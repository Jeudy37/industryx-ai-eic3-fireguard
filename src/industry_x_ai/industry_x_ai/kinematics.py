"""Cinématique directe/inverse du bras 4 axes utilisé par les robots A et B.

Convention (identique au fichier SDF généré, voir simulation/tools) :
  q1 : lacet de la tourelle (axe Z)
  q2 : épaule, angle mesuré depuis la VERTICALE (0 = bras tendu vers le haut,
       positif = penche vers l'avant)
  q3 : coude, relatif à q2
  q4 : poignet, relatif ; l'outil pointe vers le bas quand q2+q3+q4 = pi

Tous les bras sont à la position articulaire 0 au démarrage de Gazebo : bras vertical,
donc aucune collision possible à l'initialisation.
Étudiants 06 (Janvier) et 09 (Remy) : les dimensions L1, L2, H0, LG sont identiques au
modèle SDF — modifier les deux ensemble (le générateur lit ce fichier).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

Vec3 = Tuple[float, float, float]
Joints = Tuple[float, float, float, float]

L1 = 0.30   # épaule -> coude (m)
L2 = 0.30   # coude -> poignet (m)
H0 = 0.15   # hauteur de l'épaule au-dessus de la base (m)
LG = 0.10   # poignet -> point de préhension (TCP) (m)

JOINT_LIMITS = ((-3.1416, 3.1416), (-0.40, 2.20), (-0.20, 2.80), (-0.60, 3.30))


class UnreachableError(ValueError):
    """La cible est hors de l'espace atteignable du bras."""


@dataclass(frozen=True)
class ArmSpec:
    """Position/orientation de la base d'un bras dans le monde."""
    name: str
    base: Vec3
    yaw: float = 0.0

    def to_local(self, p: Vec3) -> Vec3:
        dx, dy = p[0] - self.base[0], p[1] - self.base[1]
        c, s = math.cos(-self.yaw), math.sin(-self.yaw)
        return (dx * c - dy * s, dx * s + dy * c, p[2] - self.base[2])

    def to_world(self, p: Vec3) -> Vec3:
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        return (self.base[0] + p[0] * c - p[1] * s,
                self.base[1] + p[0] * s + p[1] * c,
                self.base[2] + p[2])


def polar_tcp(spec: ArmSpec, theta: float, r: float, z_world: float) -> Vec3:
    """Point monde défini en polaire (angle local theta, rayon r) autour de la base."""
    return spec.to_world((r * math.cos(theta), r * math.sin(theta), z_world - spec.base[2]))


def inverse_kinematics(spec: ArmSpec, tcp: Vec3) -> Joints:
    """IK analytique (coude en haut, outil vertical vers le bas).

    Raises UnreachableError si la cible est hors portée ou hors limites articulaires.
    """
    lx, ly, lz = spec.to_local(tcp)
    r = math.hypot(lx, ly)
    if r < 0.08:
        raise UnreachableError(f"{spec.name}: cible trop proche de l'axe ({r:.3f} m)")
    theta = math.atan2(ly, lx)
    zw = lz + LG - H0                      # poignet par rapport à l'épaule
    d = math.hypot(r, zw)
    if d > L1 + L2 - 1e-6 or d < abs(L1 - L2) + 1e-6:
        raise UnreachableError(f"{spec.name}: cible hors portée (d={d:.3f} m)")
    cos_a = (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)
    phi1 = math.atan2(zw, r) + math.acos(max(-1.0, min(1.0, cos_a)))  # depuis l'horizontale
    ex, ez = L1 * math.cos(phi1), L1 * math.sin(phi1)
    phi2 = math.atan2(zw - ez, r - ex)
    q2 = math.pi / 2 - phi1
    alpha2 = math.pi / 2 - phi2
    q3 = alpha2 - q2
    q4 = math.pi - alpha2
    q = (theta, q2, q3, q4)
    for i, (lo, hi) in enumerate(JOINT_LIMITS):
        if not lo - 1e-9 <= q[i] <= hi + 1e-9:
            raise UnreachableError(f"{spec.name}: q{i + 1}={q[i]:.3f} hors limites [{lo}, {hi}]")
    return q


def forward_points(spec: ArmSpec, q: Joints) -> Dict[str, Vec3]:
    """Positions monde des articulations : base, shoulder, elbow, wrist, tool (TCP)."""
    q1, q2, q3, q4 = q
    a1, a2 = q2, q2 + q3
    a3 = a2 + q4
    sh = (0.0, H0)
    el = (sh[0] + L1 * math.sin(a1), sh[1] + L1 * math.cos(a1))
    wr = (el[0] + L2 * math.sin(a2), el[1] + L2 * math.cos(a2))
    tl = (wr[0] + LG * math.sin(a3), wr[1] + LG * math.cos(a3))

    def w(rz):
        return spec.to_world((rz[0] * math.cos(q1), rz[0] * math.sin(q1), rz[1]))

    return {"base": spec.to_world((0.0, 0.0, 0.0)), "shoulder": w(sh),
            "elbow": w(el), "wrist": w(wr), "tool": w(tl)}


def forward_tcp(spec: ArmSpec, q: Joints) -> Vec3:
    return forward_points(spec, q)["tool"]


def segments(spec: ArmSpec, q: Joints) -> List[Tuple[Vec3, Vec3]]:
    p = forward_points(spec, q)
    return [(p["base"], p["shoulder"]), (p["shoulder"], p["elbow"]),
            (p["elbow"], p["wrist"]), (p["wrist"], p["tool"])]

"""Génération et exécution de trajectoires articulaires (profil « minimum jerk »).

Un *plan* est une liste de pas : Move (déplacement articulaire), Pause, Grip
(fermeture/ouverture du préhenseur). Le ``PlanExecutor`` est avancé par pas de temps dt ;
il ne dépend ni de ROS ni de Gazebo : le même code tourne dans les nœuds et dans les tests.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Union

from .kinematics import Joints

VMAX = 1.4        # rad/s : vitesse articulaire moyenne cible
MIN_MOVE_T = 0.5  # s


@dataclass
class Move:
    q: Joints
    label: str = ""
    duration: float = 0.0     # calculée si 0


@dataclass
class Pause:
    duration: float = 0.3


@dataclass
class Grip:
    closed: bool
    piece_id: Optional[str] = None


Step = Union[Move, Pause, Grip]


def smooth(u: float) -> float:
    """Polynôme minimum-jerk : 0 -> 1 avec vitesse et accélération nulles aux extrémités."""
    u = min(max(u, 0.0), 1.0)
    return 10 * u ** 3 - 15 * u ** 4 + 6 * u ** 5


def move_duration(q0: Joints, q1: Joints, speed_scale: float = 1.0) -> float:
    dmax = max(abs(a - b) for a, b in zip(q0, q1))
    return max(MIN_MOVE_T, 1.875 * dmax / (VMAX * max(speed_scale, 1e-3)))


class PlanExecutor:
    """Exécute un plan pas à pas. ``step(dt)`` renvoie la liste des événements Grip déclenchés."""

    def __init__(self, q_init: Joints, speed_scale: float = 1.0):
        self.q: Joints = tuple(q_init)  # type: ignore[assignment]
        self.speed_scale = speed_scale
        self._steps: List[Step] = []
        self._i = 0
        self._t = 0.0
        self._q0: Joints = self.q
        self._label = ""

    @property
    def busy(self) -> bool:
        return self._i < len(self._steps)

    @property
    def label(self) -> str:
        return self._label

    def load(self, steps: List[Step]) -> None:
        self._steps, self._i, self._t = list(steps), 0, 0.0
        self._enter()

    def _enter(self) -> None:
        if self._i < len(self._steps) and isinstance(self._steps[self._i], Move):
            m = self._steps[self._i]
            self._q0 = self.q
            if m.duration <= 0:
                m.duration = move_duration(self._q0, m.q, self.speed_scale)
            self._label = m.label

    def step(self, dt: float) -> List[dict]:
        events: List[dict] = []
        remaining = dt
        while self.busy and remaining > 1e-12:
            s = self._steps[self._i]
            if isinstance(s, Grip):
                events.append({"type": "grip", "closed": s.closed, "piece_id": s.piece_id})
                self._i += 1
                self._enter()
                continue
            dur = s.duration
            use = min(remaining, max(dur - self._t, 0.0))
            self._t += use
            remaining -= use
            if isinstance(s, Move):
                k = smooth(self._t / dur if dur > 0 else 1.0)
                self.q = tuple(a + (b - a) * k for a, b in zip(self._q0, s.q))  # type: ignore[assignment]
            if self._t >= dur - 1e-12:
                if isinstance(s, Move):
                    self.q = tuple(s.q)  # type: ignore[assignment]
                self._i += 1
                self._t = 0.0
                self._enter()
        return events

"""Modèle logique du monde : convoyeur, génération et suivi des pièces.

Indépendant de Gazebo : le nœud ``conveyor_node`` applique les poses calculées ici dans
la simulation (service set_pose) ; ``headless_sim`` utilise ce même modèle pour valider
la logique sans interface graphique.

Cycle de vie d'une pièce : BELT -> HELD (robot A) -> TRANSFER -> HELD (robot B) -> BIN
(ou FAILED / REMOVED en cas d'erreur). La préhension est simulée par *attachement
cinématique* (la pièce suit le TCP du robot) — approche acceptée par le cahier des charges.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from . import config as C


@dataclass
class Piece:
    id: str
    color: str
    shape: str
    x: float
    y: float
    z: float
    state: str = "BELT"
    holder: Optional[str] = None
    expected_bin: str = ""
    t_spawn: float = 0.0
    bin: Optional[str] = None
    ready: bool = False
    dirty: bool = True

    def xyz(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)


class WorldModel:
    def __init__(self, total_pieces: int = 10, spawn_period: float = 8.0, randomize: bool = False,
                 seed: int = 1, grasp_failure_rate: float = 0.0):
        self.total = total_pieces
        self.spawn_period = spawn_period
        self.rng = random.Random(seed)
        self.randomize = randomize
        self.fail_rate = grasp_failure_rate
        self.pieces: Dict[str, Piece] = {}
        self.spawned = 0
        self._next_spawn = 1.0
        self.tools: Dict[str, Tuple[float, float, float]] = {}
        self.belt_running = True

    # ------------------------------------------------------------ génération
    def _next_attrs(self):
        if self.randomize:
            return self.rng.choice(list(C.COLORS)), self.rng.choice(C.SHAPES)
        return C.PIECE_PATTERN[self.spawned % len(C.PIECE_PATTERN)]

    def maybe_spawn(self, t: float) -> Optional[Piece]:
        if self.spawned >= self.total > 0 or t < self._next_spawn:
            return None
        if any(p.state == "BELT" and p.x < C.SPAWN_X + C.QUEUE_SPACING for p in self.pieces.values()):
            return None
        color, shape = self._next_attrs()
        self.spawned += 1
        p = Piece(f"piece_{self.spawned}", color, shape, C.SPAWN_X, C.BELT_Y, C.PIECE_CENTER_Z,
                  expected_bin=C.BIN_RULE[color], t_spawn=t)
        self.pieces[p.id] = p
        self._next_spawn = t + self.spawn_period
        return p

    @property
    def all_spawned(self) -> bool:
        return self.total > 0 and self.spawned >= self.total

    # ------------------------------------------------------------ pas de temps
    def step(self, t: float, dt: float) -> List[dict]:
        """Avance le convoyeur ; renvoie les événements (ready...)."""
        events: List[dict] = []
        belt = sorted((p for p in self.pieces.values() if p.state == "BELT"), key=lambda p: -p.x)
        limit = C.STOP_X
        for p in belt:
            if self.belt_running:
                new_x = min(p.x + C.BELT_SPEED * dt, limit)
                if abs(new_x - p.x) > 1e-9:
                    p.x, p.dirty = new_x, True
            limit = p.x - C.QUEUE_SPACING
            if not p.ready and p.x >= C.STOP_X - 1e-6:
                p.ready = True
                events.append({"event": "ready", "piece": p.id, "color": p.color, "shape": p.shape,
                               "pos": [p.x, p.y, p.z], "t": t})
        return events

    # ------------------------------------------------------------ préhenseur
    def tool_update(self, robot: str, xyz) -> None:
        self.tools[robot] = tuple(xyz)  # type: ignore[assignment]
        for p in self.pieces.values():
            if p.state == "HELD" and p.holder == robot:
                p.x, p.y, p.z = xyz[0], xyz[1], xyz[2] - C.PIECE_HALF
                p.dirty = True

    def grasp(self, robot: str, piece_id: str, t: float) -> dict:
        p = self.pieces.get(piece_id)
        tool = self.tools.get(robot)
        if p is None or tool is None or p.state not in ("BELT", "TRANSFER"):
            return {"event": "grasp_failed", "robot": robot, "piece": piece_id, "t": t,
                    "reason": "pièce introuvable ou non disponible"}
        dist = math.hypot(tool[0] - p.x, tool[1] - p.y)
        dz = abs((tool[2] - C.PIECE_HALF) - p.z)
        if dist > 0.04 or dz > 0.04:
            return {"event": "grasp_failed", "robot": robot, "piece": piece_id, "t": t,
                    "reason": f"pièce hors de portée du préhenseur ({dist:.3f} m)"}
        if self.rng.random() < self.fail_rate:     # injection de panne (tests de robustesse)
            return {"event": "grasp_failed", "robot": robot, "piece": piece_id, "t": t,
                    "reason": "échec de préhension injecté"}
        p.state, p.holder, p.ready = "HELD", robot, False
        return {"event": "grasped", "robot": robot, "piece": piece_id, "t": t}

    def release(self, robot: str, t: float) -> Optional[dict]:
        held = [p for p in self.pieces.values() if p.state == "HELD" and p.holder == robot]
        if not held:
            return None
        p = held[0]
        p.holder, p.dirty = None, True
        if math.hypot(p.x - C.TRANSFER_XY[0], p.y - C.TRANSFER_XY[1]) < 0.06:
            p.state, p.x, p.y, p.z = "TRANSFER", C.TRANSFER_XY[0], C.TRANSFER_XY[1], C.PIECE_CENTER_Z
            return {"event": "transferred", "robot": robot, "piece": p.id, "t": t}
        for name, (bx, by) in C.BINS.items():
            if math.hypot(p.x - bx, p.y - by) < C.BIN_SIZE / 2 - 0.02:
                p.state, p.bin = "BIN", name
                p.x, p.y, p.z = bx, by, C.BIN_FLOOR_Z + C.PIECE_HALF
                return {"event": "binned", "robot": robot, "piece": p.id, "bin": name,
                        "expected_bin": p.expected_bin, "correct": name == p.expected_bin,
                        "color": p.color, "shape": p.shape, "t": t}
        p.state = "FAILED"
        p.z = C.TABLE_TOP_Z + C.PIECE_HALF
        return {"event": "dropped", "robot": robot, "piece": p.id, "t": t}

    def remove(self, piece_id: str, t: float) -> dict:
        p = self.pieces[piece_id]
        p.state, p.holder, p.dirty = "REMOVED", None, True
        p.x, p.y, p.z = C.REJECT_XYZ
        return {"event": "removed", "piece": piece_id, "t": t}

    # ------------------------------------------------------------ poses à pousser vers Gazebo
    def pop_dirty(self) -> List[Piece]:
        out = [p for p in self.pieces.values() if p.dirty]
        for p in out:
            p.dirty = False
        return out

"""Contrôleur logique d'un bras (robot A ou B) — indépendant de ROS.

Rôle des primitives (commandes envoyées par l'orchestrateur) :
  Robot A (préhension) : PICK_BELT, PLACE_TRANSFER, HOME
  Robot B (tri)        : PICK_TRANSFER, PLACE_BIN, HOME

Chaque commande est transformée en plan : approche au-dessus -> descente -> (fermeture /
ouverture du préhenseur) -> remontée. Les waypoints sont vérifiés par IK AVANT exécution :
une cible inatteignable est refusée (état ERROR) au lieu de produire un mouvement dangereux.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional

from . import config as C
from .kinematics import Joints, UnreachableError, forward_tcp, inverse_kinematics
from .motion import Grip, Move, Pause, PlanExecutor, Step

A_COMMANDS = ("PICK_BELT", "PLACE_TRANSFER", "HOME")
B_COMMANDS = ("PICK_TRANSFER", "PLACE_BIN", "HOME")
ENTERING = {"A": "PLACE_TRANSFER", "B": "PICK_TRANSFER"}   # primitives qui entrent dans la zone T


class ArmController:
    def __init__(self, role: str, speed_scale: float = 1.0):
        if role not in ("A", "B"):
            raise ValueError("role doit être 'A' ou 'B'")
        self.role = role
        self.spec = C.SPECS[role]
        self.home_q: Joints = inverse_kinematics(self.spec, C.HOME_TCP[role])
        self.exec = PlanExecutor((0.0, 0.0, 0.0, 0.0), speed_scale)   # bras vertical au démarrage
        self.state = "BUSY"
        self.task = "INIT"
        self.cmd_id = 0
        self.last_done = -1          # -1 : initialisation pas encore terminée
        self.holding: Optional[str] = None
        self.error = ""
        self.exec.load([Move(self.home_q, "init_home")])

    # ------------------------------------------------------------ état
    @property
    def q(self) -> Joints:
        return self.exec.q

    def tool_xyz(self):
        return forward_tcp(self.spec, self.q)

    def zone(self) -> str:
        x, y, _ = self.tool_xyz()
        d = math.hypot(x - C.TRANSFER_XY[0], y - C.TRANSFER_XY[1])
        return "TRANSFER" if d < C.TRANSFER_RADIUS else "OTHER"

    def status(self) -> Dict:
        return {"robot": self.role, "state": self.state, "task": self.task,
                "cmd_id": self.cmd_id, "last_done": self.last_done, "zone": self.zone(),
                "holding": self.holding, "error": self.error}

    # ------------------------------------------------------------ commandes
    def submit(self, cmd: Dict) -> bool:
        """Accepte une commande si le bras est libre. Renvoie False sinon (la commande est ignorée)."""
        if self.state == "BUSY":
            return False
        try:
            steps = self._build_plan(cmd)
        except (UnreachableError, KeyError, ValueError) as exc:
            self.state, self.error = "ERROR", str(exc)
            self.cmd_id = int(cmd.get("cmd_id", self.cmd_id))
            return False
        self.cmd_id = int(cmd.get("cmd_id", self.cmd_id + 1))
        self.task = cmd["cmd"]
        self.state, self.error = "BUSY", ""
        self.exec.load(steps)
        return True

    def _ik(self, x: float, y: float, z: float) -> Joints:
        return inverse_kinematics(self.spec, (x, y, z))

    def _build_plan(self, cmd: Dict) -> List[Step]:
        name = cmd["cmd"]
        allowed = A_COMMANDS if self.role == "A" else B_COMMANDS
        if name not in allowed:
            raise ValueError(f"commande {name} invalide pour le robot {self.role}")
        if name == "HOME":
            steps: List[Step] = []
            if self.tool_xyz()[2] < C.Z_HOVER - 0.02:      # remonter d'abord si le TCP est bas
                steps.append(Move(self._ik(*self._above(self.exec_tool_xy(), C.Z_HOVER)), "lift"))
            return steps + [Move(self.home_q, "home")]
        if name == "PICK_BELT":
            x, y = cmd.get("pos", [C.STOP_X, C.BELT_Y])[:2]
            return self._pick(x, y, cmd["piece_id"])
        if name == "PLACE_TRANSFER":
            return self._place(*C.TRANSFER_XY, C.Z_GRASP)
        if name == "PICK_TRANSFER":
            return self._pick(*C.TRANSFER_XY, cmd["piece_id"])
        if name == "PLACE_BIN":
            bx, by = C.BINS[cmd["bin"]]
            return self._place(bx, by, C.Z_BIN_RELEASE)
        raise ValueError(name)

    def exec_tool_xy(self):
        x, y, _ = self.tool_xyz()
        return (x, y)

    @staticmethod
    def _above(xy, z):
        return (xy[0], xy[1], z)

    def _pick(self, x: float, y: float, piece_id: str) -> List[Step]:
        hov, low = self._ik(x, y, C.Z_HOVER), self._ik(x, y, C.Z_GRASP)
        return [Move(hov, "approach"), Move(low, "descend"), Pause(0.25),
                Grip(True, piece_id), Pause(0.25), Move(hov, "lift")]

    def _place(self, x: float, y: float, z_release: float) -> List[Step]:
        hov, low = self._ik(x, y, C.Z_HOVER), self._ik(x, y, z_release)
        return [Move(hov, "approach"), Move(low, "descend"), Pause(0.25),
                Grip(False), Pause(0.25), Move(hov, "lift")]

    # ------------------------------------------------------------ avancement
    def step(self, dt: float) -> List[dict]:
        """Avance de dt secondes ; renvoie les événements de préhenseur."""
        events = self.exec.step(dt)
        for ev in events:
            self.holding = ev["piece_id"] if ev["closed"] else None
        if self.state == "BUSY" and not self.exec.busy:
            self.state = "IDLE"
            if self.task == "INIT":
                self.last_done, self.task = 0, "HOME"
            else:
                self.last_done = self.cmd_id
            if self.task == "HOME":
                self.holding = None
        return events

    def clear_error(self) -> None:
        self.state, self.error = "IDLE", ""

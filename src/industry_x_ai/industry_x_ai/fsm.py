"""Machine à états centrale (orchestration) — logique PURE, sans ROS.

Étudiant 04 (DESULMA Johnsley). Le nœud ``orchestrator_node`` ne fait que relayer les
messages ROS 2 vers les méthodes de cette classe et publier les commandes retournées.

Principe (pipeline à deux postes) :
  Pièce : READY (au bout du convoyeur) -> A_HELD -> ON_TRANSFER -> B_HELD -> DONE
  Robot A : PICK_BELT, PLACE_TRANSFER, HOME        Robot B : PICK_TRANSFER, PLACE_BIN, HOME
  Les deux robots travaillent en parallèle sur des pièces différentes, sauf dans la zone
  de transfert T qui est protégée par un VERROU EXCLUSIF (``self.lock``) :
    - A ne peut entrer en T (PLACE_TRANSFER) que si T est vide ET le verrou est libre ;
    - B ne peut entrer en T (PICK_TRANSFER) que si une pièce y attend ET le verrou est libre ;
    - le verrou est libéré quand le propriétaire n'exécute plus la commande d'entrée ET que
      son TCP a quitté la zone (état publié par le robot).
  => A et B ne sont jamais ensemble dans la zone partagée : prévention des collisions par
  construction (vérifiée en continu par la distance « capsules » du nœud de supervision).

Gestion des erreurs : échec de préhension -> nouvel essai (max_retries) puis rebut de la
pièce ; commande sans réponse -> timeout, retour au repos (HOME) et libération du verrou.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from . import config as C
from .robot_controller import ENTERING

Command = Tuple[str, dict]    # (destinataire 'A' | 'B' | 'conveyor', charge utile JSON)


class Orchestrator:
    def __init__(self, bin_rule: Optional[Dict[str, str]] = None, cmd_timeout: float = 45.0,
                 classify_timeout: float = 6.0, max_retries: int = 3):
        self.bin_rule = bin_rule or dict(C.BIN_RULE)
        self.cmd_timeout = cmd_timeout
        self.classify_timeout = classify_timeout
        self.max_retries = max_retries
        self.pieces: Dict[str, dict] = {}
        self.belt_front: Optional[str] = None
        self.transfer_piece: Optional[str] = None
        self.lock: Optional[str] = None
        self.status: Dict[str, dict] = {}
        self.pending: Dict[str, Optional[dict]] = {"A": None, "B": None}
        self.needs_home = {"A": False, "B": False}
        self._cmd_seq = {"A": 0, "B": 0}
        self.started = False
        self.log: List[dict] = []          # journal des décisions (publié par le nœud)
        self.fault_count = 0

    # ================================================================ entrées
    def on_piece_ready(self, info: dict, t: float) -> None:
        pid = info["piece"]
        self.pieces[pid] = {"stage": "READY", "pos": info.get("pos", [C.STOP_X, C.BELT_Y, C.PIECE_CENTER_Z]),
                            "bin": None, "method": None, "retries": 0, "t_ready": t, "t_transfer": None}
        self.belt_front = pid
        self._log(t, "ready", piece=pid)

    def on_classification(self, info: dict, t: float) -> None:
        p = self.pieces.get(info["piece"])
        if p is not None and p["bin"] is None:
            p["bin"] = info.get("bin") or self.bin_rule.get(info.get("color", ""))
            p["method"] = info.get("method", "?")
            self._log(t, "classified", piece=info["piece"], bin=p["bin"], method=p["method"])

    def on_world_event(self, ev: dict, t: float) -> None:
        pid, name = ev.get("piece"), ev["event"]
        p = self.pieces.get(pid)
        if p is None:
            return
        if name == "grasped":
            if ev["robot"] == "A":
                p["stage"], self.belt_front = "A_HELD", None
            else:
                p["stage"], self.transfer_piece = "B_HELD", None
            p["grasp_ok"] = True
        elif name == "grasp_failed":
            p["grasp_ok"] = False
            self._log(t, "grasp_failed", piece=pid, reason=ev.get("reason", ""))
        elif name == "transferred":
            p["stage"], self.transfer_piece, p["t_transfer"] = "ON_TRANSFER", pid, t
        elif name in ("binned", "dropped"):
            p["stage"] = "DONE" if name == "binned" else "FAILED"

    def on_status(self, robot: str, st: dict, t: float) -> None:
        self.status[robot] = st
        if not self.started and all(r in self.status and self.status[r]["state"] == "IDLE"
                                    and self.status[r]["last_done"] >= 0 for r in ("A", "B")):
            self.started = True
            self._log(t, "cell_ready")
        pend = self.pending[robot]
        if pend is None:
            return
        if st["state"] == "ERROR" and st["cmd_id"] == pend["cmd_id"]:
            self._fault(robot, t, f"erreur robot : {st.get('error', '')}")
        elif st["state"] == "IDLE" and st["last_done"] >= pend["cmd_id"]:
            self.pending[robot] = None
            self._complete(robot, pend, st, t)

    # ================================================================ sorties
    def tick(self, t: float) -> List[Command]:
        out: List[Command] = []
        for r in ("A", "B"):                                  # timeouts
            pend = self.pending[r]
            if pend and t - pend["t"] > self.cmd_timeout:
                self._fault(r, t, f"timeout de la commande {pend['cmd']}")
        self._release_lock()
        if not self.started:
            return out
        out += self._decide_a(t)
        out += self._decide_b(t)
        return out

    # ================================================================ interne
    def _log(self, t: float, event: str, **kw) -> None:
        self.log.append({"t": round(t, 3), "event": event, **kw})

    def drain_log(self) -> List[dict]:
        out, self.log = self.log, []
        return out

    def _idle(self, r: str) -> bool:
        st = self.status.get(r)
        return bool(st) and st["state"] == "IDLE" and self.pending[r] is None

    def _held_by(self, stage: str) -> Optional[str]:
        return next((pid for pid, p in self.pieces.items() if p["stage"] == stage), None)

    def _send(self, r: str, cmd: str, t: float, **kw) -> Command:
        self._cmd_seq[r] += 1
        payload = {"cmd_id": self._cmd_seq[r], "cmd": cmd, **kw}
        self.pending[r] = {"cmd_id": payload["cmd_id"], "cmd": cmd, "t": t, "piece": kw.get("piece_id")}
        self._log(t, "command", robot=r, cmd=cmd, **{k: v for k, v in kw.items() if k != "pos"})
        return (r, payload)

    def _decide_a(self, t: float) -> List[Command]:
        if not self._idle("A"):
            return []
        if self.needs_home["A"]:
            self.needs_home["A"] = False
            return [self._send("A", "HOME", t)]
        held = self._held_by("A_HELD")
        if held:
            if self.lock is None and self.transfer_piece is None:
                self.lock = "A"
                return [self._send("A", "PLACE_TRANSFER", t, piece_id=held)]
            return []
        pid = self.belt_front
        if pid and self.pieces[pid]["stage"] == "READY":
            return [self._send("A", "PICK_BELT", t, piece_id=pid, pos=self.pieces[pid]["pos"])]
        return []

    def _decide_b(self, t: float) -> List[Command]:
        if not self._idle("B"):
            return []
        if self.needs_home["B"]:
            self.needs_home["B"] = False
            return [self._send("B", "HOME", t)]
        held = self._held_by("B_HELD")
        if held:
            p = self.pieces[held]
            return [self._send("B", "PLACE_BIN", t, piece_id=held, bin=p["bin"])]
        pid = self.transfer_piece
        if pid and self.lock is None:
            p = self.pieces[pid]
            if p["bin"] is None and t - (p["t_transfer"] or t) > self.classify_timeout:
                p["bin"], p["method"] = "C", "timeout"
                self._log(t, "classification_timeout", piece=pid, bin="C")
            if p["bin"] is not None:
                self.lock = "B"
                return [self._send("B", "PICK_TRANSFER", t, piece_id=pid)]
        return []

    def _complete(self, r: str, pend: dict, st: dict, t: float) -> None:
        cmd, pid = pend["cmd"], pend.get("piece")
        p = self.pieces.get(pid) if pid else None
        if cmd == "PICK_BELT" and p and p["stage"] == "READY":         # préhension ratée
            self._retry(r, pid, p, t)
        elif cmd == "PICK_TRANSFER" and p and p["stage"] == "ON_TRANSFER":
            self._retry(r, pid, p, t)
        elif cmd == "PLACE_TRANSFER":
            self.needs_home["A"] = True
        elif cmd == "PLACE_BIN":
            self.needs_home["B"] = True
        self._log(t, "done", robot=r, cmd=cmd)

    def _retry(self, r: str, pid: str, p: dict, t: float) -> None:
        p["retries"] += 1
        if p["retries"] > self.max_retries:
            p["stage"] = "FAILED"
            if self.belt_front == pid:
                self.belt_front = None
            if self.transfer_piece == pid:
                self.transfer_piece = None
            self.needs_home[r] = True
            self._log(t, "piece_abandoned", piece=pid)
            self.log.append({"t": round(t, 3), "event": "conveyor_cmd", "cmd": "REMOVE", "piece": pid})
        else:
            self.needs_home[r] = True       # retour au repos puis nouvel essai
            self._log(t, "retry", piece=pid, attempt=p["retries"])

    def _fault(self, r: str, t: float, why: str) -> None:
        self.fault_count += 1
        self.pending[r] = None
        self.needs_home[r] = True
        self._log(t, "fault", robot=r, reason=why)

    def _release_lock(self) -> None:
        o = self.lock
        if o is None:
            return
        st = self.status.get(o, {})
        pend = self.pending[o]
        entering = pend is not None and pend["cmd"] == ENTERING[o]
        if not entering and st.get("zone") != "TRANSFER":
            self.lock = None

    def drain_conveyor_commands(self) -> List[dict]:
        cmds = [{"cmd": e["cmd"], "piece_id": e["piece"]} for e in self.log if e["event"] == "conveyor_cmd"]
        self.log = [e for e in self.log if e["event"] != "conveyor_cmd"]
        return cmds

"""Simulation « sans tête » de la cellule : valide la LOGIQUE complète sans ROS ni Gazebo.

Elle assemble exactement les mêmes classes que les nœuds ROS 2 (WorldModel, ArmController,
Orchestrator, classifier, CycleLogger, distance capsules) et les fait tourner en temps
simulé accéléré. Utilité : intégration continue (GitHub Actions), tests de robustesse avec
pannes injectées, et génération reproductible d'un journal de cycles.

ATTENTION : ce n'est PAS la simulation Gazebo. Les captures/vidéo/journal « officiels »
doivent venir de la simulation Gazebo (voir docs/GUIDE_UTILISATEUR.md).

Usage : python3 -m industry_x_ai.headless_sim --pieces 10 --out tests/logs --tag nominal
"""
from __future__ import annotations

import argparse
import os
import time as _time

from . import config as C
from .classifier import classify_attributes
from .collision import min_arm_distance
from .fsm import Orchestrator
from .kinematics import segments
from .metrics import CycleLogger
from .robot_controller import ArmController
from .world_model import WorldModel


def run(pieces: int = 10, dt: float = 0.02, seed: int = 1, fail_rate: float = 0.0,
        randomize: bool = False, spawn_period: float = 8.0, max_time: float = 900.0,
        speed_scale: float = 1.0, classify_delay: float = 0.3, verbose: bool = False):
    world = WorldModel(pieces, spawn_period, randomize, seed, fail_rate)
    arms = {"A": ArmController("A", speed_scale), "B": ArmController("B", speed_scale)}
    orch = Orchestrator()
    logger = CycleLogger()
    pending_cls = []                     # (t_dispo, info) : latence de perception simulée
    t, next_status = 0.0, 0.0
    end_t = None
    while t < max_time:
        # --- convoyeur / génération
        p = world.maybe_spawn(t)
        if p:
            logger.on_world_event({"event": "spawned", "piece": p.id, "color": p.color,
                                   "shape": p.shape, "t": t})
        for ev in world.step(t, dt):
            logger.on_world_event(ev)
            orch.on_piece_ready(ev, t)
            pending_cls.append((t + classify_delay, ev))
        for item in [x for x in pending_cls if x[0] <= t]:
            pending_cls.remove(item)
            e = item[1]
            res = classify_attributes(e["color"], e["shape"])
            orch.on_classification({"piece": e["piece"], **res}, t)
        # --- bras
        for role, arm in arms.items():
            evs = arm.step(dt)
            world.tool_update(role, arm.tool_xyz())
            for g in evs:
                wev = world.grasp(role, g["piece_id"], t) if g["closed"] else world.release(role, t)
                if wev:
                    logger.on_world_event(wev)
                    orch.on_world_event(wev, t)
                    if wev["event"] == "grasp_failed":
                        arm.holding = None
        # --- statuts et commandes
        if t >= next_status:
            for role, arm in arms.items():
                orch.on_status(role, arm.status(), t)
            next_status = t + 0.1
        for target, payload in orch.tick(t):
            if target in arms and not arms[target].submit(payload):
                orch.on_status(target, arms[target].status(), t)
        for e in orch.drain_conveyor_commands():
            logger.on_world_event(world.remove(e["piece_id"], t))
        for e in orch.drain_log():
            logger.on_orchestrator_log(e)
            if verbose:
                print(f"[{t:7.2f}s] {e}")
        # --- sécurité
        d = min_arm_distance(segments(C.ROBOT_A, arms["A"].q), segments(C.ROBOT_B, arms["B"].q))
        logger.on_distance(d, C.COLLISION_DIST)
        # --- fin
        finished = world.all_spawned and all(
            pc.state in ("BIN", "FAILED", "REMOVED") for pc in world.pieces.values())
        if finished and end_t is None:
            end_t = t + 1.0
        if end_t is not None and t >= end_t:
            break
        t += dt
    return logger, world, orch, t


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pieces", type=int, default=10)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--fail-rate", type=float, default=0.0, help="probabilité d'échec de préhension injecté")
    ap.add_argument("--random", action="store_true", help="couleurs/formes aléatoires")
    ap.add_argument("--out", default="tests/logs")
    ap.add_argument("--tag", default="headless_nominal")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    t0 = _time.time()
    logger, _, _, t_end = run(a.pieces, seed=a.seed, fail_rate=a.fail_rate, randomize=a.random,
                              verbose=a.verbose)
    os.makedirs(a.out, exist_ok=True)
    logger.write_csv(os.path.join(a.out, f"{a.tag}.csv"))
    logger.write_json(os.path.join(a.out, f"{a.tag}.json"), t_end)
    print(logger.markdown_table())
    print("RÉSUMÉ :", logger.summary(t_end))
    print(f"(temps simulé {t_end:.1f} s calculé en {_time.time() - t0:.1f} s réelles)")


if __name__ == "__main__":
    main()

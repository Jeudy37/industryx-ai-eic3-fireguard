"""Journalisation des cycles et calcul des métriques (étudiant 12 — Poste B Supervision & Data).

Entrées : événements du monde ({"event": ...}) et du journal de l'orchestrateur.
Sorties : CSV par pièce, résumé JSON, tableau Markdown pour tests/.
"""
from __future__ import annotations

import csv
import json
import statistics
from typing import Dict, List, Optional

CSV_FIELDS = ["cycle", "piece_id", "color", "shape", "expected_bin", "sorted_bin", "result",
              "t_spawn", "t_ready", "t_grasp_A", "t_transfer", "t_grasp_B", "t_binned",
              "cycle_time_s", "total_time_s", "retries", "classif_method", "min_arm_dist_m"]


class CycleLogger:
    def __init__(self):
        self.rec: Dict[str, dict] = {}
        self.order: List[str] = []
        self.collision_events = 0
        self.min_distance = float("inf")
        self.faults = 0
        self.log: List[dict] = []

    def _r(self, pid: str) -> dict:
        if pid not in self.rec:
            self.rec[pid] = {"piece_id": pid, "retries": 0, "classif_method": "", "result": "EN_COURS",
                             "min_arm_dist_m": float("inf")}
            self.order.append(pid)
        return self.rec[pid]

    def on_world_event(self, ev: dict) -> None:
        name, pid, t = ev["event"], ev.get("piece"), ev.get("t", 0.0)
        if pid is None:
            return
        r = self._r(pid)
        if name == "spawned":
            r.update(color=ev["color"], shape=ev["shape"], t_spawn=t,
                     expected_bin={"red": "A", "green": "B", "blue": "C"}[ev["color"]])
        elif name == "ready":
            r["t_ready"] = t
        elif name == "grasped":
            r["t_grasp_A" if ev["robot"] == "A" else "t_grasp_B"] = t
        elif name == "transferred":
            r["t_transfer"] = t
        elif name == "binned":
            r.update(t_binned=t, sorted_bin=ev["bin"], expected_bin=ev["expected_bin"],
                     result="OK" if ev["correct"] else "ERREUR_TRI")
        elif name == "dropped":
            r.update(t_binned=t, result="ERREUR_CHUTE")
        elif name == "removed":
            r.update(result="ABANDON")

    def on_orchestrator_log(self, e: dict) -> None:
        self.log.append(e)
        if e["event"] == "classified" and e.get("piece"):
            self._r(e["piece"])["classif_method"] = e.get("method", "")
        elif e["event"] == "retry":
            self._r(e["piece"])["retries"] += 1
        elif e["event"] == "fault":
            self.faults += 1

    def on_distance(self, d: float, collision_threshold: float) -> None:
        self.min_distance = min(self.min_distance, d)
        for r in self.rec.values():
            if r["result"] == "EN_COURS" and "t_ready" in r:
                r["min_arm_dist_m"] = min(r["min_arm_dist_m"], d)
        if d < collision_threshold:
            self.collision_events += 1

    # ------------------------------------------------------------ sorties
    def rows(self) -> List[dict]:
        rows = []
        for i, pid in enumerate(self.order, 1):
            r = dict(self.rec[pid])
            r["cycle"] = i
            if "t_binned" in r and "t_ready" in r:
                r["cycle_time_s"] = round(r["t_binned"] - r["t_ready"], 2)
            if "t_binned" in r and "t_spawn" in r:
                r["total_time_s"] = round(r["t_binned"] - r["t_spawn"], 2)
            if r["min_arm_dist_m"] == float("inf"):
                r["min_arm_dist_m"] = ""
            else:
                r["min_arm_dist_m"] = round(r["min_arm_dist_m"], 3)
            for k in ("t_spawn", "t_ready", "t_grasp_A", "t_transfer", "t_grasp_B", "t_binned"):
                if k in r:
                    r[k] = round(r[k], 2)
            rows.append(r)
        return rows

    def summary(self, elapsed: Optional[float] = None) -> dict:
        rows = self.rows()
        done = [r for r in rows if r["result"] != "EN_COURS"]
        ok = [r for r in done if r["result"] == "OK"]
        times = [r["cycle_time_s"] for r in done if "cycle_time_s" in r and r["result"] in ("OK", "ERREUR_TRI")]
        per_bin = {b: sum(1 for r in rows if r.get("sorted_bin") == b) for b in "ABC"}
        out = {"pieces_processed": len(done), "success": len(ok), "errors": len(done) - len(ok),
               "success_rate_pct": round(100 * len(ok) / len(done), 1) if done else 0.0,
               "per_bin": per_bin, "faults": self.faults, "collisions": self.collision_events,
               "min_arm_distance_m": None if self.min_distance == float("inf") else round(self.min_distance, 3)}
        if times:
            out.update(cycle_mean_s=round(statistics.mean(times), 2), cycle_min_s=min(times),
                       cycle_max_s=max(times))
        if elapsed and ok:
            out["throughput_pieces_per_min"] = round(60 * len(ok) / elapsed, 2)
        return out

    def write_csv(self, path: str) -> None:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
            w.writeheader()
            w.writerows(self.rows())

    def write_json(self, path: str, elapsed: Optional[float] = None) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"summary": self.summary(elapsed), "cycles": self.rows(), "log": self.log},
                      f, ensure_ascii=False, indent=2)

    def markdown_table(self) -> str:
        head = "| # | Pièce | Couleur | Forme | Bac attendu | Bac obtenu | Résultat | Temps de cycle (s) | Reprises | Méthode |\n"
        head += "|---|---|---|---|---|---|---|---|---|---|\n"
        lines = [f"| {r['cycle']} | {r['piece_id']} | {r.get('color', '')} | {r.get('shape', '')} | "
                 f"{r.get('expected_bin', '')} | {r.get('sorted_bin', '-')} | {r['result']} | "
                 f"{r.get('cycle_time_s', '-')} | {r['retries']} | {r['classif_method']} |" for r in self.rows()]
        return head + "\n".join(lines) + "\n"

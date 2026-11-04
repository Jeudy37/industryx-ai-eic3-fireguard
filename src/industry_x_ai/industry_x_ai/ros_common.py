"""Utilitaires ROS 2 communs aux nœuds (JSON dans std_msgs/String, temps simulé)."""
import json

from std_msgs.msg import String


def to_msg(d: dict) -> String:
    m = String()
    m.data = json.dumps(d, ensure_ascii=False)
    return m


def from_msg(m: String) -> dict:
    return json.loads(m.data)


def now_s(node) -> float:
    return node.get_clock().now().nanoseconds * 1e-9


class DtClock:
    """Calcule dt à partir de l'horloge du nœud (temps simulé si use_sim_time=true)."""

    def __init__(self, node, max_dt=0.1):
        self.node, self.max_dt, self.last = node, max_dt, None

    def tick(self) -> float:
        t = now_s(self.node)
        dt = 0.0 if self.last is None else min(max(t - self.last, 0.0), self.max_dt)
        self.last = t
        return dt

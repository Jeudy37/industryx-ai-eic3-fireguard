"""Nœud d'orchestration (étudiant 04 — DESULMA Johnsley) : enveloppe ROS 2 de fsm.Orchestrator."""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .fsm import Orchestrator
from .ros_common import from_msg, now_s, to_msg


class OrchestratorNode(Node):
    def __init__(self):
        super().__init__("orchestrator_node")
        self.declare_parameters("", [("cmd_timeout", 45.0), ("classify_timeout", 6.0), ("max_retries", 3)])
        g = lambda k: self.get_parameter(k).value          # noqa: E731
        self.fsm = Orchestrator(cmd_timeout=g("cmd_timeout"), classify_timeout=g("classify_timeout"),
                                max_retries=g("max_retries"))
        self.pub = {"A": self.create_publisher(String, "/robot_a/command", 10),
                    "B": self.create_publisher(String, "/robot_b/command", 10),
                    "conveyor": self.create_publisher(String, "/conveyor/command", 10)}
        self.p_log = self.create_publisher(String, "/orchestrator/log", 50)
        self.create_subscription(String, "/world/events", self._world, 50)
        self.create_subscription(String, "/perception/classification", self._cls, 10)
        self.create_subscription(String, "/robot_a/status", lambda m: self._st("A", m), 10)
        self.create_subscription(String, "/robot_b/status", lambda m: self._st("B", m), 10)
        self.create_timer(0.1, self._tick)
        self.get_logger().info("Orchestrateur prêt : attente des deux robots au repos.")

    def _world(self, m):
        ev = from_msg(m)
        if ev["event"] == "ready":
            self.fsm.on_piece_ready(ev, now_s(self))
        else:
            self.fsm.on_world_event(ev, now_s(self))

    def _cls(self, m):
        self.fsm.on_classification(from_msg(m), now_s(self))

    def _st(self, r, m):
        self.fsm.on_status(r, from_msg(m), now_s(self))

    def _tick(self):
        for target, payload in self.fsm.tick(now_s(self)):
            self.pub[target].publish(to_msg(payload))
        for c in self.fsm.drain_conveyor_commands():
            self.pub["conveyor"].publish(to_msg(c))
        for e in self.fsm.drain_log():
            self.p_log.publish(to_msg(e))
            self.get_logger().info(f"{e['event']} " + " ".join(f"{k}={v}" for k, v in e.items() if k not in ("t", "event")))


def main(args=None):
    rclpy.init(args=args)
    node = OrchestratorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

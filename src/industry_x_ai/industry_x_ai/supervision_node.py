"""Nœud de supervision & données (étudiant 12 — Poste B).

Compteurs, temps de cycle, états des robots, distance minimale entre bras (collisions),
journal CSV/JSON et tableau de bord Web http://localhost:8080 .
"""
import os
import threading
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String

from . import config as C
from .collision import min_arm_distance
from .dashboard import start as start_dashboard
from .kinematics import segments
from .metrics import CycleLogger
from .ros_common import from_msg, now_s, to_msg


class SupervisionNode(Node):
    def __init__(self):
        super().__init__("supervision_node")
        self.declare_parameters("", [("log_dir", os.path.expanduser("~/industry_x_logs")),
                                     ("dashboard_port", 8080), ("expected_pieces", 10)])
        self.log_dir = self.get_parameter("log_dir").value or os.path.expanduser("~/industry_x_logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.tag = time.strftime("run_%Y%m%d_%H%M%S")
        self.lock = threading.Lock()
        self.logger = CycleLogger()
        self.robots, self.q = {}, {}
        self.distance = None
        self.t0 = None
        self.create_subscription(String, "/world/events", self._world, 50)
        self.create_subscription(String, "/orchestrator/log", self._olog, 50)
        for r in "AB":
            self.create_subscription(String, f"/robot_{r.lower()}/status",
                                     lambda m, role=r: self.robots.__setitem__(role, from_msg(m)), 10)
            self.create_subscription(JointState, f"/robot_{r.lower()}/joint_cmd",
                                     lambda m, role=r: self.q.__setitem__(role, tuple(m.position)), 20)
        self.p_metrics = self.create_publisher(String, "/supervision/metrics", 10)
        self.p_alert = self.create_publisher(String, "/supervision/alerts", 10)
        self.create_timer(0.05, self._safety)
        self.create_timer(1.0, self._publish)
        self.create_timer(5.0, self._save)
        try:
            self.srv = start_dashboard(self._snapshot, int(self.get_parameter("dashboard_port").value))
            self.get_logger().info(f"Tableau de bord : http://localhost:{self.get_parameter('dashboard_port').value}")
        except OSError as exc:
            self.get_logger().warn(f"Tableau de bord indisponible : {exc}")
        self.get_logger().info(f"Journaux dans {self.log_dir}/{self.tag}.*")

    def _world(self, m):
        ev = from_msg(m)
        with self.lock:
            if self.t0 is None and ev["event"] == "spawned":
                self.t0 = ev["t"]
            self.logger.on_world_event(ev)

    def _olog(self, m):
        with self.lock:
            self.logger.on_orchestrator_log(from_msg(m))

    def _safety(self):
        if "A" in self.q and "B" in self.q:
            d = min_arm_distance(segments(C.ROBOT_A, self.q["A"]), segments(C.ROBOT_B, self.q["B"]))
            self.distance = round(d, 3)
            with self.lock:
                self.logger.on_distance(d, C.COLLISION_DIST)
            if d < C.WARNING_DIST:
                self.p_alert.publish(to_msg({"alert": "PROXIMITE_BRAS", "distance_m": self.distance}))
                self.get_logger().warn(f"Bras trop proches : {d:.3f} m")

    def _snapshot(self):
        with self.lock:
            el = None if self.t0 is None else now_s(self) - self.t0
            return {"summary": self.logger.summary(el), "cycles": self.logger.rows(),
                    "robots": self.robots, "distance": self.distance}

    def _publish(self):
        s = self._snapshot()
        self.p_metrics.publish(to_msg(s["summary"]))
        sm = s["summary"]
        self.get_logger().info(f"traitées={sm['pieces_processed']} ok={sm['success']} err={sm['errors']} "
                               f"collisions={sm['collisions']} dmin={sm['min_arm_distance_m']}")

    def _save(self):
        with self.lock:
            el = None if self.t0 is None else now_s(self) - self.t0
            self.logger.write_csv(os.path.join(self.log_dir, self.tag + ".csv"))
            self.logger.write_json(os.path.join(self.log_dir, self.tag + ".json"), el)


def main(args=None):
    rclpy.init(args=args)
    node = SupervisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._save()
        node.destroy_node()
        rclpy.try_shutdown()

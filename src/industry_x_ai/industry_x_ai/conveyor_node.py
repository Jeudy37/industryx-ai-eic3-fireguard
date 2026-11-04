"""Nœud convoyeur & objets (étudiante 08 — NOËL Françoise).

Génère les pièces colorées, les fait avancer sur le convoyeur (butée au point de prise),
simule la préhension (la pièce suit le TCP du robot qui la tient) et publie les événements
du monde. La pose des pièces est appliquée dans Gazebo via le service set_pose.

Topics : sub  /robot_{a,b}/tool_pose, /robot_{a,b}/gripper, /conveyor/command
         pub  /world/events (JSON : spawned, ready, grasped, grasp_failed, transferred, binned, ...)
"""
import os
import queue
import subprocess
import tempfile
import threading

import rclpy
from geometry_msgs.msg import PointStamped
from rclpy.node import Node
from std_msgs.msg import String

from . import config as C
from .piece_model import piece_sdf
from .ros_common import DtClock, from_msg, now_s, to_msg
from .world_model import WorldModel


class GzCli:
    """Accès à Gazebo via la commande `gz service` (repli si le pont ROS n'expose pas set_pose)."""

    def __init__(self, world, logger):
        self.world, self.log = world, logger
        self.q = queue.Queue()
        self.latest = {}
        threading.Thread(target=self._worker, daemon=True).start()

    def _call(self, service, reqtype, req, timeout=3000):
        try:
            subprocess.run(["gz", "service", "-s", f"/world/{self.world}/{service}", "--reqtype", reqtype,
                            "--reptype", "gz.msgs.Boolean", "--timeout", str(timeout), "--req", req],
                           capture_output=True, timeout=8)
        except Exception as exc:        # noqa: BLE001
            self.log.warn(f"gz service {service}: {exc}")

    def spawn(self, name, color, shape, xyz):
        path = os.path.join(tempfile.gettempdir(), f"{name}.sdf")
        with open(path, "w", encoding="utf-8") as f:
            f.write(piece_sdf(name, color, shape))
        req = (f'sdf_filename: "{path}", name: "{name}", allow_renaming: false, '
               f'pose: {{position: {{x: {xyz[0]}, y: {xyz[1]}, z: {xyz[2]}}}}}')
        self.q.put(("create", "gz.msgs.EntityFactory", req))

    def set_pose(self, name, xyz):
        self.latest[name] = xyz

    def flush(self):
        for name, p in list(self.latest.items()):
            self.q.put(("set_pose", "gz.msgs.Pose", f'name: "{name}", position: {{x: {p[0]}, y: {p[1]}, z: {p[2]}}}, '
                        'orientation: {w: 1}'))
        self.latest.clear()

    def _worker(self):
        while True:
            service, reqtype, req = self.q.get()
            self._call(service, reqtype, req)


class ConveyorNode(Node):
    def __init__(self):
        super().__init__("conveyor_node")
        self.declare_parameters("", [("total_pieces", 10), ("spawn_period", 8.0), ("randomize", False),
                                     ("seed", 1), ("grasp_failure_rate", 0.0), ("pose_backend", "auto"),
                                     ("world_name", C.WORLD_NAME)])
        g = lambda k: self.get_parameter(k).value          # noqa: E731
        self.world = WorldModel(g("total_pieces"), g("spawn_period"), g("randomize"), g("seed"),
                                g("grasp_failure_rate"))
        self.pub = self.create_publisher(String, "/world/events", 50)
        for r in ("a", "b"):
            self.create_subscription(PointStamped, f"/robot_{r}/tool_pose",
                                     lambda m, role=r.upper(): self._tool(role, m), 20)
            self.create_subscription(String, f"/robot_{r}/gripper",
                                     lambda m, role=r.upper(): self._gripper(role, m), 20)
        self.create_subscription(String, "/conveyor/command", self._command, 10)
        self.dtc = DtClock(self)
        self.backend = g("pose_backend")
        self.cli = GzCli(g("world_name"), self.get_logger()) if self.backend != "mock" else None
        self.srv_client, self.inflight = None, 0
        if self.backend in ("auto", "bridge"):
            self._init_bridge(g("world_name"))
        self.t_push = 0.0
        self.create_timer(1 / 30, self._tick)
        self.get_logger().info(f"Convoyeur prêt (backend de pose : {self.backend}, "
                               f"{g('total_pieces')} pièces).")

    # ------------------------------------------------------------ backend de pose
    def _init_bridge(self, world):
        try:
            from ros_gz_interfaces.srv import SetEntityPose
            self._SetEntityPose = SetEntityPose
            self.srv_client = self.create_client(SetEntityPose, f"/world/{world}/set_pose")
            if not self.srv_client.wait_for_service(timeout_sec=5.0):
                raise RuntimeError("service set_pose du pont indisponible")
            self.backend = "bridge"
        except Exception as exc:             # noqa: BLE001
            self.get_logger().warn(f"Pont set_pose indisponible ({exc}) -> repli sur `gz service`.")
            self.srv_client, self.backend = None, "gz_cli"

    def _apply_pose(self, p):
        if self.backend == "mock":
            return
        if self.backend == "bridge":
            if self.inflight > 60:
                return
            req = self._SetEntityPose.Request()
            req.entity.name, req.entity.type = p.id, 2           # 2 = MODEL
            req.pose.position.x, req.pose.position.y, req.pose.position.z = p.x, p.y, p.z
            req.pose.orientation.w = 1.0
            self.inflight += 1
            self.srv_client.call_async(req).add_done_callback(lambda _f: setattr(self, "inflight", self.inflight - 1))
        else:
            self.cli.set_pose(p.id, p.xyz())

    # ------------------------------------------------------------ callbacks
    def _emit(self, ev):
        self.pub.publish(to_msg(ev))

    def _tool(self, role, m):
        self.world.tool_update(role, (m.point.x, m.point.y, m.point.z))

    def _gripper(self, role, m):
        d, t = from_msg(m), now_s(self)
        ev = self.world.grasp(role, d["piece_id"], t) if d["closed"] else self.world.release(role, t)
        if ev:
            self._emit(ev)
            self.get_logger().info(f"{ev['event']} {ev.get('piece')} {ev.get('bin', '')}")

    def _command(self, m):
        d = from_msg(m)
        if d.get("cmd") == "REMOVE" and d.get("piece_id") in self.world.pieces:
            self._emit(self.world.remove(d["piece_id"], now_s(self)))

    def _tick(self):
        t, dt = now_s(self), self.dtc.tick()
        if dt <= 0.0:
            return
        p = self.world.maybe_spawn(t)
        if p:
            self._emit({"event": "spawned", "piece": p.id, "color": p.color, "shape": p.shape, "t": t})
            if self.backend != "mock":
                if self.backend == "bridge" and self.cli is None:
                    self.cli = GzCli(self.get_parameter("world_name").value, self.get_logger())
                self.cli.spawn(p.id, p.color, p.shape, p.xyz())
        for ev in self.world.step(t, dt):
            self._emit(ev)
        for p in self.world.pop_dirty():
            self._apply_pose(p)
        if self.backend == "gz_cli" and t - self.t_push > 0.2:
            self.cli.flush()
            self.t_push = t


def main(args=None):
    rclpy.init(args=args)
    node = ConveyorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

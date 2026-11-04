"""Nœud générique d'un bras (robot A ou B) — enveloppe ROS 2 de ``ArmController``.

Étudiants 02 (APPOLON — programmation robot A) et 01 (ALTIDOR — programmation robot B).

Sub  /robot_x/command (JSON)       Pub  /robot_x/status (JSON, 10 Hz)
Pub  /robot_x/tool_pose (PointStamped, 50 Hz)   /robot_x/gripper (JSON, sur changement)
Pub  /robot_x/joint_cmd (JointState, 50 Hz)      /robot_x/j{1..4}/cmd (Float64 -> Gazebo)
"""
import rclpy
from geometry_msgs.msg import PointStamped
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64, String

from .robot_controller import ArmController
from .ros_common import DtClock, from_msg, to_msg


class RobotNode(Node):
    def __init__(self, role: str):
        super().__init__(f"robot_{role.lower()}_node")
        self.declare_parameter("speed_scale", 1.0)
        self.role, self.ns = role, f"/robot_{role.lower()}"
        self.arm = ArmController(role, self.get_parameter("speed_scale").value)
        self.cmd_pubs = [self.create_publisher(Float64, f"{self.ns}/j{i}/cmd", 10) for i in range(1, 5)]
        self.p_status = self.create_publisher(String, f"{self.ns}/status", 10)
        self.p_tool = self.create_publisher(PointStamped, f"{self.ns}/tool_pose", 10)
        self.p_grip = self.create_publisher(String, f"{self.ns}/gripper", 10)
        self.p_js = self.create_publisher(JointState, f"{self.ns}/joint_cmd", 10)
        self.create_subscription(String, f"{self.ns}/command", self._on_command, 10)
        self.dtc = DtClock(self)
        self.create_timer(0.02, self._tick)
        self.create_timer(0.1, self._status)
        self.get_logger().info(f"Robot {role} initialisé (retour en position repos…).")

    def _on_command(self, msg: String) -> None:
        cmd = from_msg(msg)
        ok = self.arm.submit(cmd)
        self.get_logger().info(f"Commande {cmd['cmd']} #{cmd.get('cmd_id')} "
                               f"{'acceptée' if ok else 'REFUSÉE ' + self.arm.error}")
        self._status()

    def _tick(self) -> None:
        dt = self.dtc.tick()
        for ev in self.arm.step(dt):
            self.p_grip.publish(to_msg({"closed": ev["closed"], "piece_id": ev["piece_id"]}))
        stamp = self.get_clock().now().to_msg()
        for pub, v in zip(self.cmd_pubs, self.arm.q):
            pub.publish(Float64(data=float(v)))
        x, y, z = self.arm.tool_xyz()
        tp = PointStamped()
        tp.header.stamp, tp.header.frame_id = stamp, "world"
        tp.point.x, tp.point.y, tp.point.z = x, y, z
        self.p_tool.publish(tp)
        js = JointState()
        js.header.stamp = stamp
        js.name = [f"{self.ns[1:]}_joint{i}" for i in range(1, 5)]
        js.position = [float(v) for v in self.arm.q]
        self.p_js.publish(js)

    def _status(self) -> None:
        self.p_status.publish(to_msg(self.arm.status()))


def run(role, args=None):
    rclpy.init(args=args)
    node = RobotNode(role)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

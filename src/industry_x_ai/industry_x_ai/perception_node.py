"""Nœud perception / IA (étudiant 05 — DIEUYEL Jean Jeudy).

Modes (paramètre ``mode``) :
  attributes : règle classique à partir des attributs du capteur simulé (fiable, MVP) ;
  opencv     : classification par caméra virtuelle (HSV + contours), repli sur attributs si la
               caméra ne répond pas dans ``camera_timeout`` secondes ;
  compare    : décision par OpenCV, et l'accord avec la règle classique est publié sur
               /perception/stats (comparaison IA vs règle exigée par le cahier des charges).
"""
from collections import Counter

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String

from .classifier import classify_attributes, classify_image
from .ros_common import from_msg, now_s, to_msg


class PerceptionNode(Node):
    def __init__(self):
        super().__init__("perception_node")
        self.declare_parameters("", [("mode", "attributes"), ("camera_timeout", 4.0), ("frames", 3)])
        self.mode = self.get_parameter("mode").value
        self.pub = self.create_publisher(String, "/perception/classification", 10)
        self.p_stats = self.create_publisher(String, "/perception/stats", 10)
        self.create_subscription(String, "/world/events", self._events, 50)
        if self.mode != "attributes":
            self.create_subscription(Image, "/camera/image", self._image, 5)
        self.job = None
        self.agree = self.total = 0
        self.create_timer(0.2, self._timeout)
        self.get_logger().info(f"Perception en mode « {self.mode} ».")

    def _events(self, m):
        ev = from_msg(m)
        if ev["event"] != "ready":
            return
        attr = classify_attributes(ev["color"], ev["shape"])
        if self.mode == "attributes":
            self._publish(ev["piece"], attr, attr)
        else:
            self.job = {"piece": ev["piece"], "t": now_s(self), "attr": attr, "votes": [], "skip": 3}

    def _image(self, msg):
        if not self.job:
            return
        if self.job["skip"] > 0:               # laisse la pièce se stabiliser sous la caméra
            self.job["skip"] -= 1
            return
        img = np.frombuffer(bytes(msg.data), np.uint8).reshape(msg.height, msg.step)[:, : msg.width * 3]
        res = classify_image(img.reshape(msg.height, msg.width, 3))
        if res:
            self.job["votes"].append(res)
        if len(self.job["votes"]) >= self.get_parameter("frames").value:
            best = Counter((v["color"], v["shape"]) for v in self.job["votes"]).most_common(1)[0][0]
            res = next(v for v in self.job["votes"] if (v["color"], v["shape"]) == best)
            self._publish(self.job["piece"], res, self.job["attr"])

    def _timeout(self):
        if self.job and now_s(self) - self.job["t"] > self.get_parameter("camera_timeout").value:
            self.get_logger().warn("Caméra sans résultat -> repli sur la règle par attributs.")
            fb = dict(self.job["attr"], method="attributs (repli)")
            self._publish(self.job["piece"], fb, self.job["attr"])

    def _publish(self, piece, res, attr):
        self.job = None
        self.pub.publish(to_msg({"piece": piece, **res, "attr_bin": attr["bin"]}))
        if res["method"] == "opencv":
            self.total += 1
            self.agree += int(res["bin"] == attr["bin"])
            self.p_stats.publish(to_msg({"opencv_vs_rule_agreement": self.agree, "total": self.total}))


def main(args=None):
    rclpy.init(args=args)
    node = PerceptionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

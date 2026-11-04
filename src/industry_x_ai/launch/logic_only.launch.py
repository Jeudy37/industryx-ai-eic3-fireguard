"""Logique seule (sans Gazebo) : orchestrateur, robots, convoyeur « mock », supervision.

Utile pour tester la coordination sur n'importe quelle machine ROS 2 (ou en intégration continue)
et pour voir le tableau de bord http://localhost:8080 :   ros2 launch industry_x_ai logic_only.launch.py
"""
from pathlib import Path

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    params = str(Path(__file__).resolve().parents[1] / "config" / "params.yaml")
    mock = {"use_sim_time": False}

    def node(exe, extra=None):
        return Node(package="industry_x_ai", executable=exe, name=exe, output="screen",
                    parameters=[params, mock] + ([extra] if extra else []))
    return LaunchDescription([node("robot_a_node"), node("robot_b_node"), node("orchestrator_node"),
                              node("perception_node"), node("supervision_node"),
                              node("conveyor_node", {"pose_backend": "mock", "spawn_period": 4.0})])

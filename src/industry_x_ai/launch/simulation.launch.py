"""Lancement complet : Gazebo Harmonic + ponts ROS<->Gazebo + tous les nœuds INDUSTRY-X AI.

    ros2 launch industry_x_ai simulation.launch.py
    ros2 launch industry_x_ai simulation.launch.py perception_mode:=opencv total_pieces:=10
    ros2 launch industry_x_ai simulation.launch.py headless:=true       # sans fenêtre Gazebo

Le dossier simulation/ est trouvé via la variable INDUSTRY_X_SIM_DIR (positionnée par
scripts/run_simulation.sh) ou, avec `colcon build --symlink-install`, depuis les sources.
"""
import os
from pathlib import Path

from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, ExecuteProcess, SetEnvironmentVariable, TimerAction)
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def _sim_dir() -> Path:
    env = os.environ.get("INDUSTRY_X_SIM_DIR")
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "simulation" / "worlds").is_dir():
            return parent / "simulation"
    raise RuntimeError("Dossier simulation/ introuvable : définir INDUSTRY_X_SIM_DIR "
                       "ou compiler avec `colcon build --symlink-install`.")


def generate_launch_description():
    sim = _sim_dir()
    world = str(sim / "worlds" / "industry_x.world")
    params = str(Path(__file__).resolve().parents[1] / "config" / "params.yaml")
    if not os.path.exists(params):
        from ament_index_python.packages import get_package_share_directory
        params = os.path.join(get_package_share_directory("industry_x_ai"), "config", "params.yaml")

    args = [
        DeclareLaunchArgument("headless", default_value="false", description="true = Gazebo sans interface"),
        DeclareLaunchArgument("perception_mode", default_value="attributes", description="attributes|opencv|compare"),
        DeclareLaunchArgument("total_pieces", default_value="10"),
        DeclareLaunchArgument("grasp_failure_rate", default_value="0.0"),
        DeclareLaunchArgument("pose_backend", default_value="auto", description="auto|bridge|gz_cli"),
        DeclareLaunchArgument("dashboard_port", default_value="8080"),
        DeclareLaunchArgument("log_dir", default_value=""),
    ]
    res_path = os.pathsep.join(filter(None, [str(sim / "models"), os.environ.get("GZ_SIM_RESOURCE_PATH", "")]))
    env = SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", res_path)

    gz_full = ExecuteProcess(cmd=["gz", "sim", "-r", world], output="screen",
                             condition=__import__("launch.conditions", fromlist=["x"]).UnlessCondition(LaunchConfiguration("headless")))
    gz_head = ExecuteProcess(cmd=["gz", "sim", "-r", "-s", "--headless-rendering", world], output="screen",
                             condition=__import__("launch.conditions", fromlist=["x"]).IfCondition(LaunchConfiguration("headless")))

    topics = ["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
              "/camera/image@sensor_msgs/msg/Image[gz.msgs.Image"]
    for r in ("a", "b"):
        topics += [f"/robot_{r}/j{i}/cmd@std_msgs/msg/Float64]gz.msgs.Double" for i in range(1, 5)]
    bridge = Node(package="ros_gz_bridge", executable="parameter_bridge", arguments=topics,
                  name="gz_bridge", output="screen", parameters=[{"use_sim_time": False}])
    bridge_srv = Node(package="ros_gz_bridge", executable="parameter_bridge", name="gz_service_bridge",
                      arguments=["/world/industry_x/set_pose@ros_gz_interfaces/srv/SetEntityPose"],
                      output="screen")

    sim_time = {"use_sim_time": True}

    def node(exe, extra=None):
        return Node(package="industry_x_ai", executable=exe, name=exe, output="screen",
                    parameters=[params, sim_time] + ([extra] if extra else []))

    nodes = [
        node("robot_a_node"), node("robot_b_node"), node("orchestrator_node"),
        node("perception_node", {"mode": ParameterValue(LaunchConfiguration("perception_mode"), value_type=str)}),
        node("supervision_node", {"dashboard_port": ParameterValue(LaunchConfiguration("dashboard_port"), value_type=int),
                                  "log_dir": ParameterValue(LaunchConfiguration("log_dir"), value_type=str)}),
        node("conveyor_node", {"total_pieces": ParameterValue(LaunchConfiguration("total_pieces"), value_type=int),
                               "grasp_failure_rate": ParameterValue(LaunchConfiguration("grasp_failure_rate"), value_type=float),
                               "pose_backend": ParameterValue(LaunchConfiguration("pose_backend"), value_type=str)}),
    ]
    # on laisse 6 s à Gazebo pour charger le monde avant de démarrer la logique
    return LaunchDescription(args + [env, gz_full, gz_head, bridge, bridge_srv, TimerAction(period=6.0, actions=nodes)])

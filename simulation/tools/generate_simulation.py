#!/usr/bin/env python3
"""Génère le monde Gazebo et les modèles SDF à partir de src/industry_x_ai/industry_x_ai/config.py.

    python3 simulation/tools/generate_simulation.py

Géométrie et logique de commande partagent ainsi la MÊME source de vérité (config.py,
kinematics.py). Étudiants 03 (monde), 06 et 09 (modèles de bras), 08 (convoyeur).
Choix de conception : bras 4 axes simples (visuels, sans gravité, commandés en position
par le plugin JointPositionController) — voir docs/architecture/CHOIX_TECHNIQUES.md.
"""
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src", "industry_x_ai"))

from industry_x_ai import config as C          # noqa: E402
from industry_x_ai import kinematics as K      # noqa: E402

SIM = os.path.join(ROOT, "simulation")


def mat(rgb, a=1.0):
    r, g, b = rgb
    return (f"<material><ambient>{r} {g} {b} {a}</ambient><diffuse>{r} {g} {b} {a}</diffuse>"
            f"<specular>0.2 0.2 0.2 1</specular></material>")


def box_visual(name, size, pos, rgb, collision=False):
    sx, sy, sz = size
    geom = f"<geometry><box><size>{sx} {sy} {sz}</size></box></geometry>"
    p = f"<pose>{pos[0]} {pos[1]} {pos[2]} 0 0 0</pose>"
    col = f'<collision name="{name}_c">{p}{geom}</collision>' if collision else ""
    return f'<visual name="{name}">{p}{geom}{mat(rgb)}</visual>{col}'


def static_box_model(name, size, pos, rgb):
    return (f'<model name="{name}"><static>true</static><pose>{pos[0]} {pos[1]} {pos[2]} 0 0 0</pose>'
            f'<link name="l">{box_visual("v", size, (0, 0, 0), rgb, True)}</link></model>')


# ---------------------------------------------------------------- robot
def link(name, z, visuals):
    inert = ("<inertial><mass>0.5</mass><inertia><ixx>0.01</ixx><iyy>0.01</iyy><izz>0.01</izz>"
             "</inertia></inertial>")
    return (f'<link name="{name}"><pose>0 0 {z} 0 0 0</pose><gravity>false</gravity>{inert}{visuals}</link>')


def joint(name, parent, child, axis, lim):
    return (f'<joint name="{name}" type="revolute"><parent>{parent}</parent><child>{child}</child>'
            f'<axis><xyz>{axis}</xyz><limit><lower>{lim[0]}</lower><upper>{lim[1]}</upper>'
            f'<effort>50</effort><velocity>3</velocity></limit><dynamics><damping>0.5</damping></dynamics></axis></joint>')


def robot_sdf(role, rgb):
    ns = f"robot_{role.lower()}"
    L1, L2, H0, LG = K.L1, K.L2, K.H0, K.LG
    dark, accent = (0.2, 0.2, 0.25), (0.95, 0.85, 0.1)
    cyl = lambda n, r, l, z, c: (f'<visual name="{n}"><pose>0 0 {z} 0 0 0</pose><geometry><cylinder><radius>{r}</radius>'  # noqa: E731
                                 f'<length>{l}</length></cylinder></geometry>{mat(c)}</visual>')
    sph = lambda n, r, z, c: (f'<visual name="{n}"><pose>0 0 {z} 0 0 0</pose><geometry><sphere><radius>{r}</radius>'  # noqa: E731
                              f'</sphere></geometry>{mat(c)}</visual>')
    links = [
        link("base_link", 0, cyl("plate", 0.09, 0.03, 0.015, dark)),
        link("turret", 0, cyl("column", 0.05, H0, H0 / 2, rgb) + sph("shoulder_ball", 0.055, H0, dark)),
        link("upper_arm", H0, box_visual("v", (0.06, 0.06, L1), (0, 0, L1 / 2), rgb) + sph("elbow_ball", 0.045, L1, dark)),
        link("forearm", H0 + L1, box_visual("v", (0.05, 0.05, L2), (0, 0, L2 / 2), rgb) + sph("wrist_ball", 0.04, L2, dark)),
        link("gripper", H0 + L1 + L2, box_visual("v", (0.03, 0.03, LG), (0, 0, LG / 2), accent)
             + box_visual("pad", (0.07, 0.015, 0.012), (0, 0, LG - 0.006), dark)),
    ]
    lim = K.JOINT_LIMITS
    joints = [
        '<joint name="world_fix" type="fixed"><parent>world</parent><child>base_link</child></joint>',
        joint("joint1", "base_link", "turret", "0 0 1", lim[0]),
        joint("joint2", "turret", "upper_arm", "0 1 0", lim[1]),
        joint("joint3", "upper_arm", "forearm", "0 1 0", lim[2]),
        joint("joint4", "forearm", "gripper", "0 1 0", lim[3]),
    ]
    plugins = "".join(
        f'<plugin filename="gz-sim-joint-position-controller-system" name="gz::sim::systems::JointPositionController">'
        f'<joint_name>joint{i}</joint_name><topic>/{ns}/j{i}/cmd</topic><p_gain>80</p_gain><i_gain>0</i_gain>'
        f'<d_gain>8</d_gain><cmd_max>50</cmd_max><cmd_min>-50</cmd_min></plugin>' for i in range(1, 5))
    plugins += '<plugin filename="gz-sim-joint-state-publisher-system" name="gz::sim::systems::JointStatePublisher"/>'
    return (f'<?xml version="1.0"?>\n<sdf version="1.9">\n<model name="{ns}">\n' + "\n".join(links + joints)
            + "\n" + plugins + "\n</model>\n</sdf>\n")


def model_config(name, desc):
    return (f'<?xml version="1.0"?>\n<model><name>{name}</name><version>1.0</version><sdf version="1.9">model.sdf</sdf>'
            f'<author><name>FIREGUARD-X</name></author><description>{desc}</description></model>\n')


# ---------------------------------------------------------------- monde
def bin_model(name, center, rgb):
    s, h, t = C.BIN_SIZE, C.BIN_WALL_H, 0.01
    zf, zw = C.TABLE_TOP_Z + t / 2, C.BIN_FLOOR_Z + h / 2
    parts = [box_visual("floor", (s, s, t), (0, 0, zf - 0.0), rgb, True)]
    for nm, size, pos in [("w1", (s, t, h), (0, s / 2 - t / 2, zw)), ("w2", (s, t, h), (0, -s / 2 + t / 2, zw)),
                          ("w3", (t, s, h), (s / 2 - t / 2, 0, zw)), ("w4", (t, s, h), (-s / 2 + t / 2, 0, zw))]:
        parts.append(box_visual(nm, size, pos, rgb, True))
    return (f'<model name="bin_{name}"><static>true</static><pose>{center[0]} {center[1]} 0 0 0 0</pose>'
            f'<link name="l">{"".join(parts)}</link></model>')


def conveyor_model():
    x0, x1 = C.BELT_X_MIN, C.BELT_X_MAX
    length, cx = x1 - x0, (x0 + x1) / 2
    top, w = C.TABLE_TOP_Z, C.BELT_WIDTH
    parts = [box_visual("body", (length, w, top - 0.02), (0, 0, (top - 0.02) / 2), (0.25, 0.25, 0.28), True),
             box_visual("belt", (length - 0.04, w - 0.04, 0.02), (0, 0, top - 0.01), (0.12, 0.12, 0.13), True),
             box_visual("rail_l", (length, 0.015, 0.03), (0, w / 2 - 0.0075, top + 0.015), (0.8, 0.8, 0.8), True),
             box_visual("rail_r", (length, 0.015, 0.03), (0, -w / 2 + 0.0075, top + 0.015), (0.8, 0.8, 0.8), True)]
    n = int(length / 0.10)
    for i in range(n):                         # chevrons/rainures du tapis
        parts.append(box_visual(f"groove{i}", (0.012, w - 0.06, 0.003), (-length / 2 + 0.05 + i * 0.10, 0, top + 0.0015),
                                (0.3, 0.3, 0.32)))
    parts.append(box_visual("stopper", (0.012, w - 0.04, 0.05), (C.STOP_X + 0.06 - cx, 0, top + 0.025), (0.9, 0.2, 0.2), True))
    return (f'<model name="conveyor"><static>true</static><pose>{cx} {C.BELT_Y} 0 0 0 0</pose>'
            f'<link name="l">{"".join(parts)}</link></model>')


def camera_model():
    return ('<model name="overhead_camera"><static>true</static><pose>%s %s 1.0 0 1.5708 0</pose><link name="l">'
            '<visual name="body"><geometry><box><size>0.06 0.06 0.06</size></box></geometry>%s</visual>'
            '<sensor name="cam" type="camera"><always_on>1</always_on><update_rate>10</update_rate>'
            '<topic>/camera/image</topic><camera><horizontal_fov>1.0</horizontal_fov>'
            '<image><width>320</width><height>240</height><format>R8G8B8</format></image>'
            '<clip><near>0.1</near><far>3</far></clip></camera></sensor></link></model>'
            % (C.STOP_X, C.BELT_Y, mat((0.1, 0.1, 0.1))))


def world_sdf():
    tx0, tx1, ty0, ty1 = C.TABLE_BOX
    table = static_box_model("work_table", (tx1 - tx0, ty1 - ty0, C.TABLE_TOP_Z),
                             ((tx0 + tx1) / 2, (ty0 + ty1) / 2, C.TABLE_TOP_Z / 2), (0.55, 0.55, 0.58))
    ped_a = static_box_model("pedestal_a", (0.24, 0.24, C.TABLE_TOP_Z), (C.ROBOT_A.base[0], C.ROBOT_A.base[1], C.TABLE_TOP_Z / 2),
                             (0.45, 0.45, 0.48))
    pad = static_box_model("transfer_pad", (0.12, 0.12, 0.004), (C.TRANSFER_XY[0], C.TRANSFER_XY[1], C.TABLE_TOP_Z + 0.002),
                           (0.95, 0.8, 0.1))
    bins = "\n".join(bin_model(n, c, C.BIN_COLORS[n]) for n, c in C.BINS.items())
    incl = "\n".join(
        f'<include><uri>model://robot_arm_{r.lower()}</uri><name>robot_{r.lower()}</name>'
        f'<pose>{s.base[0]} {s.base[1]} {s.base[2]} 0 0 {s.yaw}</pose></include>' for r, s in C.SPECS.items())
    return f"""<?xml version="1.0"?>
<!-- GÉNÉRÉ par simulation/tools/generate_simulation.py — ne pas éditer à la main -->
<sdf version="1.9">
  <world name="{C.WORLD_NAME}">
    <physics name="1ms" type="ode"><max_step_size>0.002</max_step_size><real_time_factor>1.0</real_time_factor></physics>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors"><render_engine>ogre2</render_engine></plugin>
    <scene><ambient>0.5 0.5 0.5 1</ambient><background>0.78 0.85 0.95 1</background><shadows>true</shadows></scene>
    <light type="directional" name="sun"><cast_shadows>true</cast_shadows><pose>0 0 6 0 0 0</pose>
      <diffuse>0.9 0.9 0.9 1</diffuse><specular>0.3 0.3 0.3 1</specular><direction>-0.4 0.3 -0.9</direction></light>
    <model name="ground"><static>true</static><link name="l">
      <collision name="c"><geometry><plane><normal>0 0 1</normal><size>20 20</size></plane></geometry></collision>
      <visual name="v"><geometry><plane><normal>0 0 1</normal><size>20 20</size></plane></geometry>{mat((0.62, 0.64, 0.66))}</visual>
    </link></model>
    {table}
    {ped_a}
    {conveyor_model()}
    {pad}
    {bins}
    {camera_model()}
    {incl}
  </world>
</sdf>
"""


def main():
    os.makedirs(os.path.join(SIM, "worlds"), exist_ok=True)
    for role, rgb in (("A", (0.95, 0.5, 0.1)), ("B", (0.45, 0.3, 0.8))):
        d = os.path.join(SIM, "models", f"robot_arm_{role.lower()}")
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "model.sdf"), "w", encoding="utf-8").write(robot_sdf(role, rgb))
        open(os.path.join(d, "model.config"), "w", encoding="utf-8").write(
            model_config(f"robot_arm_{role.lower()}", f"Bras 4 axes du robot {role}"))
    open(os.path.join(SIM, "worlds", "industry_x.world"), "w", encoding="utf-8").write(world_sdf())
    print("Monde et modèles générés dans", SIM)


if __name__ == "__main__":
    main()

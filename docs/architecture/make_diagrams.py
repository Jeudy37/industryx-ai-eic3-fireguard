#!/usr/bin/env python3
"""Régénère les schémas d'architecture (PNG) : python3 docs/architecture/make_diagrams.py"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src", "industry_x_ai"))
from industry_x_ai import config as C   # noqa: E402
from industry_x_ai import kinematics as K   # noqa: E402

OUT = os.path.dirname(__file__)
NAVY, GOLD = "#1b3a7a", "#f2a50c"


def layout():
    fig, ax = plt.subplots(figsize=(11, 6.2))
    ax.set_aspect("equal")
    x0, x1, y0, y1 = C.TABLE_BOX
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#d9dde3", ec="#8a93a0", label="Table"))
    ax.add_patch(Rectangle((C.BELT_X_MIN, -C.BELT_WIDTH / 2), C.BELT_X_MAX - C.BELT_X_MIN, C.BELT_WIDTH, fc="#3a3a40", ec="k"))
    ax.annotate("", xy=(C.STOP_X - 0.05, 0), xytext=(C.SPAWN_X, 0), arrowprops=dict(arrowstyle="->", color="w", lw=2))
    ax.text(-0.55, 0.0, "convoyeur  0,10 m/s", color="w", ha="center", va="bottom", fontsize=9)
    ax.plot(*C.SPAWN_X and (C.SPAWN_X, 0), "o", color="#ddd")
    ax.text(C.SPAWN_X, -0.22, "apparition", ha="center", fontsize=8)
    ax.plot(C.STOP_X, 0, "s", color="#e33", ms=9)
    ax.text(C.STOP_X, -0.24, "butée = point de prise", ha="center", fontsize=8, color="#c22")
    for role, spec, col in (("A", C.ROBOT_A, "#f28c1c"), ("B", C.ROBOT_B, "#7355cc")):
        ax.add_patch(Circle(spec.base[:2], 0.06, fc=col, ec="k", zorder=5))
        ax.text(spec.base[0], spec.base[1] + 0.09, f"Robot {role}", ha="center", fontweight="bold", color=col)
        ax.add_patch(Circle(spec.base[:2], K.L1 + K.L2, fill=False, ls=":", ec=col, alpha=.6))
    ax.add_patch(Circle(C.TRANSFER_XY, C.TRANSFER_RADIUS, fc=GOLD, alpha=.18, ec=GOLD, ls="--"))
    ax.add_patch(Rectangle((C.TRANSFER_XY[0] - .06, C.TRANSFER_XY[1] - .06), .12, .12, fc=GOLD, ec="k"))
    ax.text(C.TRANSFER_XY[0], C.TRANSFER_XY[1] + .33, "zone de transfert T (verrou exclusif)", ha="center", fontsize=8)
    for n, (bx, by) in C.BINS.items():
        r, g, b = C.BIN_COLORS[n]
        ax.add_patch(Rectangle((bx - .1, by - .1), .2, .2, fc=(r, g, b), ec="k", alpha=.85))
        ax.text(bx, by, f"bac {n}", ha="center", va="center", color="w", fontweight="bold", fontsize=9)
    ax.set_xlim(-1.25, 1.75); ax.set_ylim(-0.4, 1.15)
    ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
    ax.set_title("INDUSTRY-X AI — implantation de la cellule (vue de dessus, repère monde)\n"
                 "pointillés : portée max. de chaque bras (0,6 m)", fontsize=11, color=NAVY)
    ax.grid(alpha=.25)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "implantation_cellule.png"), dpi=150); plt.close(fig)


def box(ax, x, y, w, h, text, fc):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=fc, ec=NAVY, lw=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8.5)


def arrow(ax, a, b, label="", rad=0.0):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=12, color=NAVY, lw=1.2,
                                 connectionstyle=f"arc3,rad={rad}"))
    if label:
        ax.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + .02, label, fontsize=7, ha="center", color="#333",
                bbox=dict(fc="w", ec="none", pad=0.5))


def architecture():
    fig, ax = plt.subplots(figsize=(12, 6.6))
    ax.axis("off"); ax.set_xlim(0, 12); ax.set_ylim(0, 6.6)
    # bus ROS 2 central
    ax.add_patch(FancyBboxPatch((0.3, 3.05), 11.4, 0.5, boxstyle="round,pad=0.02", fc=NAVY, ec=NAVY))
    ax.text(6, 3.3, "BUS ROS 2 (topics)  /world/events · /robot_x/command · /robot_x/status · /robot_x/tool_pose · /robot_x/gripper · "
            "/perception/classification · /orchestrator/log", color="w", ha="center", va="center", fontsize=8)
    top = [("orchestrator_node\nmachine à états\n+ verrou zone T", "#ffe9b8"), ("perception_node\nattributs | OpenCV\n| compare", "#d8e8ff"),
           ("supervision_node\nmétriques, CSV/JSON,\ndistance bras, dashboard :8080", "#d9f2d9")]
    for i, (t, c) in enumerate(top):
        x = 0.5 + i * 3.9
        box(ax, x, 4.6, 3.3, 1.3, t, c)
        ax.add_patch(FancyArrowPatch((x + 1.65, 4.6), (x + 1.65, 3.55), arrowstyle="<|-|>", mutation_scale=12, color=NAVY, lw=1.4))
    bot = [("robot_a_node\nPICK_BELT\nPLACE_TRANSFER", "#fbd3b0"), ("robot_b_node\nPICK_TRANSFER\nPLACE_BIN", "#d9cff5"),
           ("conveyor_node\nconvoyeur, pièces,\npréhension simulée", "#f0e0c8")]
    for i, (t, c) in enumerate(bot):
        x = 0.5 + i * 3.9
        box(ax, x, 1.55, 3.3, 1.2, t, c)
        ax.add_patch(FancyArrowPatch((x + 1.65, 2.75), (x + 1.65, 3.05), arrowstyle="<|-|>", mutation_scale=12, color=NAVY, lw=1.4))
    box(ax, 0.5, 0.1, 11.0, 0.9, "ros_gz_bridge + Gazebo Harmonic — industry_x.world : bras A/B (JointPositionController /robot_x/jN/cmd), "
        "convoyeur, bacs A/B/C,\ncaméra zénithale (/camera/image), service set_pose (pièces)", "#e3e3e3")
    for i in range(3):
        x = 2.15 + i * 3.9
        ax.add_patch(FancyArrowPatch((x, 1.55), (x, 1.0), arrowstyle="<|-|>", mutation_scale=12, color="#555", lw=1.2))
    ax.set_title("Architecture logicielle INDUSTRY-X AI (ROS 2 Jazzy ↔ Gazebo Harmonic)", color=NAVY, fontsize=12)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "architecture_logicielle.png"), dpi=150); plt.close(fig)


def fsm():
    fig, ax = plt.subplots(figsize=(12, 4.2))
    ax.axis("off"); ax.set_xlim(0, 12); ax.set_ylim(0, 4.2)
    st = [("READY\n(butée)", 0.2, "#fff3d0"), ("A_HELD\n(A tient)", 2.5, "#fbd3b0"), ("ON_TRANSFER\n(en T)", 4.8, "#ffe9b8"),
          ("B_HELD\n(B tient)", 7.1, "#d9cff5"), ("DONE\n(dans un bac)", 9.4, "#d9f2d9")]
    for t, x, c in st:
        box(ax, x, 2.4, 2.0, 1.0, t, c)
    cmds = ["A: PICK_BELT", "A: PLACE_TRANSFER\n(verrou A)", "B: PICK_TRANSFER\n(verrou B)", "B: PLACE_BIN\n(bac selon couleur)"]
    for i in range(4):
        arrow(ax, (st[i][1] + 2.0, 2.9), (st[i + 1][1], 2.9), "")
        ax.text(st[i][1] + 2.1, 3.65, cmds[i], fontsize=7.5, ha="center")
    box(ax, 2.5, 0.4, 7.0, 1.2, "Échec de préhension -> HOME puis nouvel essai (max 3) -> rebut\n"
        "Timeout de commande (45 s) -> défaut, HOME, verrou libéré\nPas de classification en 6 s -> bac C par défaut (journalisé)", "#fde0e0")
    ax.set_title("États d'une pièce et primitives des robots", color=NAVY)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "machine_a_etats.png"), dpi=150); plt.close(fig)


if __name__ == "__main__":
    layout(); architecture(); fsm(); print("schémas régénérés")

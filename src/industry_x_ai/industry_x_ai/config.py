"""Géométrie et paramètres globaux de la cellule — SOURCE UNIQUE DE VÉRITÉ.

Repère monde Gazebo, unités SI (mètres, secondes, radians). Le générateur
simulation/tools/generate_simulation.py lit ce fichier pour produire le monde et
les modèles : géométrie du code et de la simulation restent donc cohérentes.

Disposition (vue de dessus, x vers la droite, y vers le haut) :
  - convoyeur le long de l'axe x (y=0), butée / point de prise en (0, 0) ;
  - robot A en (0, 0.45), robot B en (1.0, 0.45), tourné de 180° ;
  - zone de transfert T en (0.5, 0.45), entre les deux robots ;
  - bacs A, B, C sur un cercle de rayon 0.5 m autour du robot B.
"""
import math

from .kinematics import ArmSpec, polar_tcp

# ---------------------------------------------------------------- hauteurs
TABLE_TOP_Z = 0.40            # dessus convoyeur / table / socle robot A
PIECE_SIZE = 0.06
PIECE_HALF = PIECE_SIZE / 2
PIECE_CENTER_Z = TABLE_TOP_Z + PIECE_HALF          # centre d'une pièce posée
BIN_FLOOR_Z = TABLE_TOP_Z + 0.01
BIN_SIZE = 0.20
BIN_WALL_H = 0.08

# ---------------------------------------------------------------- convoyeur
BELT_Y = 0.0
SPAWN_X = -1.00               # apparition des pièces
STOP_X = 0.00                 # butée = point de prise du robot A
BELT_SPEED = 0.10             # m/s
QUEUE_SPACING = 0.12          # distance mini entre deux pièces
BELT_X_MIN, BELT_X_MAX, BELT_WIDTH = -1.10, 0.30, 0.30
REJECT_XYZ = (-1.40, 0.80, PIECE_CENTER_Z)   # zone de rebut (pièce en échec définitif)

# ---------------------------------------------------------------- robots
ROBOT_A = ArmSpec("robot_a", (0.0, 0.45, TABLE_TOP_Z), 0.0)
ROBOT_B = ArmSpec("robot_b", (1.0, 0.45, TABLE_TOP_Z), math.pi)   # tourné de 180°
SPECS = {"A": ROBOT_A, "B": ROBOT_B}

TRANSFER_XY = (0.50, 0.45)    # zone intermédiaire entre A et B
TRANSFER_RADIUS = 0.30        # rayon de la zone protégée par le verrou
_BIN_R, _B = 0.50, ROBOT_B.base
BINS = {                      # centres des bacs : cercle de rayon 0.5 m autour de B
    "A": (_B[0] - _BIN_R * math.cos(math.pi / 4), _B[1] - _BIN_R * math.sin(math.pi / 4)),
    "B": (_B[0], _B[1] - _BIN_R),
    "C": (_B[0] + _BIN_R * math.cos(math.pi / 4), _B[1] - _BIN_R * math.sin(math.pi / 4)),
}
BIN_COLORS = {"A": (0.85, 0.15, 0.15), "B": (0.15, 0.65, 0.25), "C": (0.15, 0.30, 0.85)}
TABLE_BOX = (0.35, 1.55, -0.20, 0.70)     # xmin, xmax, ymin, ymax de la grande table

# ---------------------------------------------------------------- points de passage
# TCP = centre de la face supérieure de la pièce tenue.
Z_HOVER = 0.62
Z_GRASP = PIECE_CENTER_Z + PIECE_HALF          # 0.46
Z_BIN_RELEASE = 0.52
HOME_TCP = {
    "A": polar_tcp(ROBOT_A, -math.pi / 4, 0.30, Z_HOVER),
    "B": polar_tcp(ROBOT_B, math.pi / 2, 0.30, Z_HOVER),
}

# ---------------------------------------------------------------- classification
COLORS = {"red": (0.90, 0.10, 0.10), "green": (0.10, 0.70, 0.20), "blue": (0.10, 0.30, 0.90)}
BIN_RULE = {"red": "A", "green": "B", "blue": "C"}    # tri par COULEUR (la forme est journalisée)
SHAPES = ("cube", "cylinder")
PIECE_PATTERN = [("red", "cube"), ("green", "cylinder"), ("blue", "cube"),
                 ("red", "cylinder"), ("green", "cube"), ("blue", "cylinder")]

# ---------------------------------------------------------------- sécurité
CAPSULE_RADIUS = 0.04          # rayon d'un segment de bras (m)
COLLISION_DIST = 2 * CAPSULE_RADIUS        # sous cette distance axe-à-axe : contact
WARNING_DIST = COLLISION_DIST + 0.03       # alerte de proximité

WORLD_NAME = "industry_x"

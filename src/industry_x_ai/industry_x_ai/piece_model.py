"""Génération du SDF d'une pièce (cube ou cylindre coloré) pour Gazebo.

Les pièces sont des corps dynamiques SANS gravité et SANS collision : leur pose est pilotée
cinématiquement (convoyeur + préhension simulée). Cela garantit un comportement déterministe.
"""
from . import config as C


def piece_sdf(name: str, color: str, shape: str) -> str:
    r, g, b = C.COLORS[color]
    s = C.PIECE_SIZE
    geom = (f"<box><size>{s} {s} {s}</size></box>" if shape == "cube"
            else f"<cylinder><radius>{s / 2}</radius><length>{s}</length></cylinder>")
    mat = (f"<ambient>{r} {g} {b} 1</ambient><diffuse>{r} {g} {b} 1</diffuse>"
           f"<specular>0.1 0.1 0.1 1</specular>")
    return f"""<?xml version="1.0"?>
<sdf version="1.9">
  <model name="{name}">
    <link name="link">
      <gravity>false</gravity>
      <inertial><mass>0.1</mass><inertia><ixx>1e-4</ixx><iyy>1e-4</iyy><izz>1e-4</izz></inertia></inertial>
      <visual name="v"><geometry>{geom}</geometry><material>{mat}</material></visual>
    </link>
  </model>
</sdf>
"""

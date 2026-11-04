"""Classification des pièces : règle par attributs ET vision artificielle OpenCV (bonus IA).

Étudiant 05 (DIEUYEL Jean Jeudy).

Deux méthodes comparables (le cahier des charges demande de comparer l'IA à une règle classique) :
  1. ``classify_attributes`` : règle classique — l'attribut « couleur » fourni par le capteur
     simulé du convoyeur donne directement le bac.
  2. ``classify_image`` : perception par caméra — segmentation HSV + analyse de contour
     (couleur dominante, forme par rectangularité) sur l'image de la caméra zénithale.
"""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np

from . import config as C

try:                                    # OpenCV est optionnel : le mode « attributs » marche sans
    import cv2
except ImportError:                     # pragma: no cover
    cv2 = None


def classify_attributes(color: str, shape: str, rule: Optional[Dict[str, str]] = None) -> Dict:
    rule = rule or C.BIN_RULE
    return {"color": color, "shape": shape, "bin": rule.get(color), "confidence": 1.0,
            "method": "attributs"}


def _hue_to_color(h: float) -> Optional[str]:
    """Teinte OpenCV (0-179) -> nom de couleur."""
    if h < 10 or h >= 165:
        return "red"
    if 35 <= h <= 85:
        return "green"
    if 95 <= h <= 135:
        return "blue"
    return None


def classify_image(rgb: np.ndarray, rule: Optional[Dict[str, str]] = None,
                   min_area: int = 150) -> Optional[Dict]:
    """Classe la pièce visible dans une image RGB (H x W x 3, uint8). None si rien de détecté."""
    if cv2 is None:
        raise RuntimeError("OpenCV (cv2) n'est pas installé : sudo apt install python3-opencv")
    rule = rule or C.BIN_RULE
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    mask = ((hsv[:, :, 1] > 110) & (hsv[:, :, 2] > 50)).astype(np.uint8) * 255   # pixels colorés
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) >= min_area]
    if not contours:
        return None
    cnt = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(cnt)
    blob = np.zeros(mask.shape, np.uint8)
    cv2.drawContours(blob, [cnt], -1, 255, -1)
    h_vals = hsv[:, :, 0][blob > 0]
    # teinte circulaire : on vote par couleur pour gérer le rouge (autour de 0/180)
    votes: Dict[str, int] = {}
    for h in h_vals[:: max(1, len(h_vals) // 400)]:
        c = _hue_to_color(float(h))
        if c:
            votes[c] = votes.get(c, 0) + 1
    if not votes:
        return None
    color = max(votes, key=votes.get)                       # type: ignore[arg-type]
    confidence = votes[color] / sum(votes.values())
    x, y, w, h = cv2.boundingRect(cnt)
    extent = area / float(w * h)                            # carré ~1.0 ; disque ~0.785
    shape = "cube" if extent > 0.90 else "cylinder"
    return {"color": color, "shape": shape, "bin": rule.get(color), "confidence": round(confidence, 3),
            "method": "opencv", "area_px": int(area), "extent": round(extent, 3)}

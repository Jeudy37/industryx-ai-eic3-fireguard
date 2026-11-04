#!/usr/bin/env python3
"""Génère presentation/INDUSTRY_X_AI_Soutenance.pdf (10 diapositives, 16:9).
    python3 presentation/make_slides.py
"""
import json
import os

from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("F", D + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("FB", D + "DejaVuSans-Bold.ttf"))
W, H = 960, 540
NAVY, GOLD, LIGHT, GREY = HexColor("#1b3a7a"), HexColor("#f2a50c"), HexColor("#eef2fa"), HexColor("#444444")
n = json.load(open(os.path.join(ROOT, "tests/logs/headless_nominal.json")))["summary"]
r = json.load(open(os.path.join(ROOT, "tests/logs/headless_robustesse_pannes.json")))
rs = r["summary"]
retries = sum(c["retries"] for c in r["cycles"])
c = canvas.Canvas(os.path.join(ROOT, "presentation/INDUSTRY_X_AI_Soutenance.pdf"), pagesize=(W, H))
c.setTitle("INDUSTRY-X AI — Soutenance EIC 3.0 — FIREGUARD-X")
page = [0]


def slide(title, who=""):
    page[0] += 1
    c.setFillColor(white); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(NAVY); c.rect(0, H - 70, W, 70, fill=1, stroke=0)
    c.setFillColor(GOLD); c.rect(0, H - 74, W, 4, fill=1, stroke=0)
    c.setFillColor(white); c.setFont("FB", 26); c.drawString(36, H - 47, title)
    c.setFillColor(GREY); c.setFont("F", 10)
    c.drawString(36, 16, "INDUSTRY-X AI · EIC 3.0 · FIREGUARD-X")
    c.drawRightString(W - 36, 16, f"{who}   {page[0]}/10" if who else f"{page[0]}/10")


def bullets(items, x=44, y=H - 110, size=17, gap=11, width=870):
    for it in items:
        sub = it.startswith("  ")
        t = it.strip()
        c.setFillColor(GOLD if not sub else NAVY); c.setFont("FB", size)
        c.drawString(x + (26 if sub else 0), y, "•" if not sub else "–")
        c.setFillColor(HexColor("#1d1d1d")); c.setFont("F", size - (2 if sub else 0))
        words, line = t.split(), ""
        for w in words:
            if pdfmetrics.stringWidth(line + " " + w, "F", size) > width - (26 if sub else 0) - 24:
                c.drawString(x + 18 + (26 if sub else 0), y, line.strip()); y -= size + 5; line = w
            else:
                line += " " + w
        c.drawString(x + 18 + (26 if sub else 0), y, line.strip())
        y -= size + gap
    return y


def img(path, x, y, w, h):
    ir = ImageReader(os.path.join(ROOT, path))
    iw, ih = ir.getSize()
    s = min(w / iw, h / ih)
    c.drawImage(ir, x + (w - iw * s) / 2, y + (h - ih * s) / 2, iw * s, ih * s, mask="auto")


def box(x, y, w, h, title, lines, fill=LIGHT):
    c.setFillColor(fill); c.roundRect(x, y, w, h, 8, fill=1, stroke=0)
    c.setFillColor(NAVY); c.setFont("FB", 14); c.drawString(x + 12, y + h - 24, title)
    c.setFillColor(HexColor("#222")); c.setFont("F", 12)
    yy = y + h - 44
    for l in lines:
        c.drawString(x + 12, yy, l); yy -= 17


# 1 ---------------------------------------------------------------- titre
page[0] += 1
c.setFillColor(NAVY); c.rect(0, 0, W, H, fill=1, stroke=0)
c.setFillColor(GOLD); c.rect(0, 250, W, 5, fill=1, stroke=0)
c.setFillColor(white); c.setFont("FB", 54); c.drawString(60, 340, "INDUSTRY-X AI")
c.setFont("F", 24); c.drawString(60, 295, "Cellule industrielle virtuelle de tri d'objets")
c.setFont("F", 17)
for i, t in enumerate(["Deux bras robotisés · convoyeur · supervision · vision OpenCV",
                       "ROS 2 Jazzy · Gazebo Harmonic · Ubuntu 24.04 · Python 3.12",
                       "", "EIC 3.0 · Robotique & IA · Professeur : Carlos Yfrazin",
                       "Équipe FIREGUARD-X (12 étudiants) · Soutenance du 4 novembre 2026, 16h"]):
    c.drawString(60, 215 - i * 28, t)
c.showPage()

# 2 ---------------------------------------------------------------- objectif
slide("Objectif et exigences", "10 · 04")
bullets(["Concevoir, simuler et programmer une cellule de tri en environnement 3D, 100 % open source",
         "Robot A : détecte la pièce sur le convoyeur, la saisit et la transfère en zone intermédiaire",
         "Robot B : reprend la pièce, la classe (couleur/forme) et la dépose dans le bac A, B ou C",
         "Supervision : état des robots, comptage, temps de cycle, classification automatique",
         "Contraintes : Ubuntu 24.04 · ROS 2 Jazzy · Gazebo Harmonic · Python 3.12 · GitFlow · OpenCV (bonus IA)",
         "Évaluation : démo 3D en direct, code ROS 2, 2 bras sans collision, tri + logs + robustesse, documentation, oral"], size=19, gap=16)
c.showPage()

# 3 ---------------------------------------------------------------- implantation
slide("Implantation de la cellule", "03 · 08")
img("docs/architecture/implantation_cellule.png", 30, 40, 560, 410)
box(610, 250, 316, 190, "Choix de géométrie", ["• Bras A (0 ; 0,45) et B (1,0 ; 0,45)", "• Zone de transfert T entre les deux", "• Bacs sur un cercle de 0,5 m autour de B",
                                              "• Convoyeur 0,10 m/s, butée en (0 ; 0)", "• Tout est défini dans config.py"])
box(610, 60, 316, 170, "Une seule source de vérité", ["config.py → générateur SDF", "→ monde Gazebo + code", "toujours cohérents", "(simulation/tools/)"])
c.showPage()

# 4 ---------------------------------------------------------------- architecture
slide("Architecture logicielle", "04 · 12")
img("docs/architecture/architecture_logicielle.png", 40, 95, 880, 360)
c.setFillColor(GREY); c.setFont("F", 13)
c.drawString(40, 70, "Logique = modules Python purs (testables sans ROS) · nœuds ROS 2 = enveloppes fines · 6 nœuds · messages JSON")
c.showPage()

# 5 ---------------------------------------------------------------- bras
slide("Bras robotisés et cinématique", "06 · 09 · 02 · 01")
bullets(["Bras 4 axes : tourelle, épaule, coude, poignet — L1 = L2 = 0,30 m, outil toujours vertical",
         "Cinématique inverse analytique (coude en haut) ; limites articulaires vérifiées",
         "Une cible inatteignable est refusée AVANT le mouvement (état ERROR)",
         "Trajectoires « minimum jerk » : vitesse et accélération nulles aux extrémités",
         "Primitives : A = PICK_BELT, PLACE_TRANSFER · B = PICK_TRANSFER, PLACE_BIN · HOME",
         "Commande Gazebo : JointPositionController sur chaque axe via ros_gz_bridge",
         "Position articulaire 0 = bras vertical → aucun risque de collision au démarrage"], size=17, gap=12)
c.showPage()

# 6 ---------------------------------------------------------------- coordination
slide("Coordination et prévention des collisions", "04")
img("docs/architecture/machine_a_etats.png", 30, 270, 900, 190)
box(36, 50, 290, 200, "1. Verrou exclusif en zone T", ["A et B ne sont jamais ensemble", "dans la zone de transfert", "(testé : exclusion mutuelle)"])
box(335, 50, 290, 200, "2. IK validée avant mouvement", ["cible hors portée → refus", "limites articulaires", "poses sûres testées (toutes A×B)"])
box(634, 50, 290, 200, "3. Surveillance en continu", ["distance minimale entre capsules", "alerte < 0,11 m · contact < 0,08 m", "enregistrée dans les logs"])
c.showPage()

# 7 ---------------------------------------------------------------- perception
slide("Perception et IA (bonus OpenCV)", "05")
bullets(["Deux méthodes comparables : règle par attributs (référence) et vision OpenCV",
         "Caméra zénithale Gazebo 320×240 sur le point de prise",
         "Segmentation HSV (pixels saturés) → plus grand contour → couleur dominante par vote",
         "Forme : rectangularité du contour (carré ≈ 1,0 ; disque ≈ 0,79) → cube / cylindre",
         "Vote sur 3 images ; repli automatique sur les attributs si la caméra ne répond pas",
         "Mode compare : accord IA/règle publié sur /perception/stats",
         "Tests : 3 couleurs × 2 formes × avec/sans bruit — tous réussis"], size=17, gap=12)
c.showPage()

# 8 ---------------------------------------------------------------- résultats
slide("Tests et résultats", "07 · 12")
box(36, 270, 440, 200, "Run nominal — 10 pièces (logique)", [f"• Réussite : {n['success']}/{n['pieces_processed']} ({n['success_rate_pct']} %)",
    f"• Bacs : A={n['per_bin']['A']} · B={n['per_bin']['B']} · C={n['per_bin']['C']}", f"• Collisions : {n['collisions']}",
    f"• Distance min. bras : {n['min_arm_distance_m']} m", f"• Cycle moyen : {n['cycle_mean_s']} s · débit {n['throughput_pieces_per_min']} pièces/min"])
box(490, 270, 434, 200, "Robustesse — 25 % de pannes injectées", [f"• Reprises automatiques : {retries}", f"• Pièces traitées : {rs['pieces_processed']}/10 · réussies : {rs['success']}",
    f"• Collisions : {rs['collisions']} · défauts : {rs['faults']}", "• Aucun blocage de la cellule"])
box(36, 70, 888, 180, "Méthode", ["• 44 tests automatisés (pytest) + intégration continue GitHub Actions",
    "• Chiffres ci-dessus : simulation logique « headless » (mêmes classes que les nœuds ROS 2)",
    "• Run Gazebo réel (10 cycles) : tests/JOURNAL_10_CYCLES.md section B · captures · vidéo",
    "• Cycle = arrivée à la butée → dépôt dans le bac (inclut l'attente du robot A / du verrou)"])
c.showPage()

# 9 ---------------------------------------------------------------- équipe
slide("Équipe, Git et planning", "10")
rows = [("01 ALTIDOR", "Robot B"), ("02 APPOLON", "Robot A"), ("03 BADIO", "Monde Gazebo"), ("04 DESULMA", "Orchestration"), ("05 DIEUYEL", "Perception / IA"),
        ("06 JANVIER", "Config Robot B"), ("07 LUMERANT", "Tests & soutenance"), ("08 NOËL", "Convoyeur & objets"), ("09 REMY", "Config Robot A"),
        ("10 SAINT-PRÉVIL", "Coordination & Git"), ("11 Poste A", "Installation"), ("12 Poste B", "Supervision & data")]
for i, (a, b) in enumerate(rows):
    x, y = 36 + (i % 2) * 300, H - 120 - (i // 2) * 52
    c.setFillColor(LIGHT); c.roundRect(x, y - 8, 288, 42, 6, fill=1, stroke=0)
    c.setFillColor(NAVY); c.setFont("FB", 13); c.drawString(x + 10, y + 14, a)
    c.setFillColor(GREY); c.setFont("F", 12); c.drawString(x + 10, y - 1, b)
bullets(["GitFlow : main ← develop ← feature/*", "Pull Requests relues, CI verte", "CONTRIBUTIONS.md : 1 module = 1 responsable",
         "Planning J1-J15 · vidéo preuve J7-J8"], x=655, y=H - 125, size=15, gap=10, width=270)
c.showPage()

# 10 --------------------------------------------------------------- conclusion
slide("Conclusion et perspectives", "10 · 07")
bullets(["Cellule complète : convoyeur, 2 bras, tri 3 catégories, supervision, vision OpenCV",
         "Coordination sûre : verrou exclusif + IK validée + surveillance des distances",
         "Reproductible : 3 commandes, tests automatisés, dépôt documenté",
         "Limites assumées : préhension par attachement cinématique, pièces sans physique de contact",
         "Perspectives : préhenseur physique (DetachableJoint), MoveIt 2, bras UR5, apprentissage (CNN) pour la perception, interfaces ROS typées",
         "Démonstration en direct, puis questions"], size=18, gap=15)
c.showPage()
c.save()
print("PDF généré")

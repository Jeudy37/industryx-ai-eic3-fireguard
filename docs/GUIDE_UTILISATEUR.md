# Guide utilisateur et checklist de validation

## 1. Lancer la démonstration
```bash
bash scripts/run_simulation.sh                       # démo standard (10 pièces)
bash scripts/run_simulation.sh perception_mode:=opencv
```
1. Gazebo s'ouvre (monde `industry_x`). Pendant 6 s rien ne bouge : chargement.
2. Les deux bras passent de la position verticale à leur position repos, puis l'orchestrateur affiche `cell_ready`.
3. Une pièce apparaît toutes les 8 s à gauche du convoyeur, avance, s'arrête à la butée.
4. Robot A (orange) la saisit → la pose sur la plaque jaune (zone T) → revient au repos.
5. Robot B (violet) la reprend → la dépose dans le bac rouge (A), vert (B) ou bleu (C) selon sa couleur.
6. Ouvrir **http://localhost:8080** : compteurs, états robots, distance entre bras, derniers cycles.
7. Fin de run : `~/industry_x_logs/run_AAAAMMJJ_HHMMSS.csv|json` (recopier dans `tests/logs/`).

Arrêt : `Ctrl+C` dans le terminal du lancement.

## 2. Observer le système ROS 2
```bash
source install/setup.bash
ros2 topic echo /orchestrator/log          # décisions de la machine à états
ros2 topic echo /world/events              # événements (ready, grasped, binned…)
ros2 topic echo /supervision/metrics
ros2 topic echo /robot_a/status
rqt_graph                                  # capture d'architecture réelle (capture n°3)
```

## 3. ✅ Checklist de validation du PREMIER lancement dans Gazebo
Le monde SDF, les modèles et le lancement ont été produits et vérifiés (XML valide, géométrie/IK testées) mais
le **premier passage dans Gazebo doit être fait par l'équipe**. Cocher dans l'ordre ; en cas d'échec, voir « Réglages ».

- [ ] `bash scripts/build.sh` se termine sans erreur
- [ ] Gazebo s'ouvre : table grise, convoyeur sombre, 3 bacs colorés, plaque jaune, 2 bras **verticaux** (début)
- [ ] `ros2 topic list` contient `/clock`, `/camera/image`, `/robot_a/j1/cmd` … `/robot_b/j4/cmd`
- [ ] Les bras rejoignent la position repos sans osciller
- [ ] `/orchestrator/log` affiche `cell_ready`
- [ ] Une pièce **apparaît** au début du convoyeur (sinon voir « Réglages » 2)
- [ ] La pièce avance et s'arrête à la butée (carré rouge), événement `ready`
- [ ] A saisit : la pièce **suit** le préhenseur ; dépôt sur la plaque jaune (`transferred`)
- [ ] B saisit et dépose dans le bon bac (`binned … correct: true`)
- [ ] 10 pièces : dashboard `Réussites = 10`, `Collisions = 0`

### Réglages si un point échoue
1. **Bras oscillants / en retard** : dans `simulation/tools/generate_simulation.py`, ligne `JointPositionController`, essayer
   `p_gain` 40–150 et `d_gain` 4–15 ; ou ralentir : paramètre `speed_scale: 0.7` (params.yaml). Relancer `scripts/build.sh`.
2. **Pièces absentes ou immobiles** : lire le log de `conveyor_node`. Le nœud tente le service du pont (`bridge`) puis bascule seul sur
   `gz service` (`gz_cli`). Forcer : `pose_backend:=gz_cli`. Tester à la main :
   `gz service -s /world/industry_x/set_pose --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 300 --req 'name: "piece_1", position: {x: 0.0, y: 0.0, z: 0.8}'`
3. **Caméra sans image** (mode opencv) : `ros2 topic hz /camera/image` ; sans GPU utiliser `perception_mode:=attributes`
   (le nœud bascule seul sur les attributs après `camera_timeout`).
4. **Pièce décalée du préhenseur** : vérifier que `Z_GRASP` / `PIECE_CENTER_Z` (config.py) correspondent à la hauteur du convoyeur dans le monde.

## 4. Produire les livrables de preuve (à faire pendant un run Gazebo)
| Livrable | Comment |
|---|---|
| **Journal de 10 cycles** | Après un run complet : `cp ~/industry_x_logs/run_*.csv tests/logs/gazebo_run_01.csv` puis compléter `tests/JOURNAL_10_CYCLES.md` (section B) |
| **Captures (min. 8)** | Voir `docs/captures/README.md` (liste imposée, noms de fichiers) |
| **Vidéo 3-5 min** | `video/SCRIPT_VIDEO.md` ; enregistrement : Ctrl+Alt+Maj+R (GNOME) ou OBS Studio ; déposer sur YouTube (non répertorié) et coller le lien dans `video/README.md` |
| **Vidéo preuve J7-J8** | Un cycle complet A→T→B→bac, 60-90 s, envoyée au professeur |
| **Remise** | E-mail à Carlos.yfrasin@uniq.edu avant le 03/11/2026 23h59, objet exact : `EIC 3.0 INDUSTRY-X AI Groupe FIREGUARD-X Remise finale`, avec lien GitHub + lien vidéo |

## 5. Plan B pour la soutenance (démonstration en direct)
1. Lancer la simulation **10 min avant** la soutenance et vérifier la checklist.
2. Si Gazebo plante : `bash scripts/run_simulation.sh headless:=true` + dashboard, ou `ros2 launch industry_x_ai logic_only.launch.py`.
3. Dernier recours : vidéo de démonstration + `bash scripts/run_tests.sh` (tests et journaux logiques en 10 s).

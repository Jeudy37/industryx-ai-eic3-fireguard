# Guide d'installation — Ubuntu 24.04 · ROS 2 Jazzy · Gazebo Harmonic

*Responsable : Poste A (Installation & Config).*

## 1. Prérequis
- Ubuntu **24.04 LTS** (natif ou double démarrage ; une VM fonctionne mais Gazebo y est lent — allouer 4 cœurs, 8 Go de RAM, accélération 3D).
- 15 Go libres, connexion Internet. Aucun logiciel payant, aucun matériel.

## 2. Installation automatique (recommandée)
```bash
git clone https://github.com/<organisation>/industry-x-ai-eic3-fireguard.git && cd industry-x-ai-eic3-fireguard
bash scripts/install_ubuntu_ros2_gazebo.sh
```
Le script : (1) configure la locale UTF-8, (2) ajoute le dépôt ROS 2, (3) installe `ros-jazzy-desktop` et colcon,
(4) installe Gazebo Harmonic via `ros-jazzy-ros-gz*`, (5) installe `python3-opencv`, `python3-numpy`, `pytest`, (6) initialise rosdep.

## 3. Vérifications
```bash
lsb_release -d                 # Ubuntu 24.04 LTS
printenv ROS_DISTRO            # jazzy
ros2 --version                 # ros2 ...
gz sim --version               # Gazebo Sim, version 8.x (Harmonic)
python3 --version              # Python 3.12.x
python3 -c "import cv2; print(cv2.__version__)"
ros2 pkg list | grep ros_gz    # ros_gz_bridge, ros_gz_interfaces, ros_gz_sim
```

## 4. Compilation et premier lancement
```bash
bash scripts/build.sh          # colcon build --symlink-install + génération du monde SDF
bash scripts/run_simulation.sh
```

## 5. Installation manuelle (si le script échoue)
Suivre la documentation officielle : ROS 2 Jazzy (docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html) puis
`sudo apt install ros-jazzy-ros-gz`. Puis `sudo apt install python3-opencv python3-numpy python3-pytest`.

## 6. Problèmes fréquents
| Problème | Solution |
|---|---|
| `E: Unable to locate package ros-jazzy-...` | Dépôt ROS absent : relancer l'étape 2 du script, puis `sudo apt update` |
| `gz sim` s'ouvre mais l'écran reste noir | Pilotes graphiques : `LIBGL_ALWAYS_SOFTWARE=1 bash scripts/run_simulation.sh` (lent) ou `headless:=true` |
| `colcon: command not found` | `sudo apt install python3-colcon-common-extensions` |
| VM très lente | Réduire la qualité : `perception_mode:=attributes` (pas de caméra), `headless:=true` + dashboard |
| Conflit Python (venv/conda actif) | `conda deactivate` / `deactivate` avant `colcon build` — ROS 2 utilise le Python système 3.12 |

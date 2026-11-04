# Contributions des 12 membres — FIREGUARD-X
| N° | Étudiant | Rôle | Livrable | Fichiers principaux | Commits / PR |
|---|---|---|---|---|---|
| 01 | ALTIDOR Jean Sterlin | Programmation Robot B | Code ROS 2 de tri et dépose dans les bacs A/B/C | `robot_b_node.py`, primitives `PICK_TRANSFER` / `PLACE_BIN` dans `robot_controller.py` | … |
| 02 | APPOLON Youvens | Programmation Robot A | Code ROS 2 de préhension (pick) et transfert | `robot_a_node.py`, primitives `PICK_BELT` / `PLACE_TRANSFER`, `motion.py` | … |
| 03 | BADIO Dany | Monde Gazebo | Fichier de monde 3D (.world), sol, éclairage, bacs | `simulation/worlds/industry_x.world`, `simulation/tools/generate_simulation.py` (fonctions `world_sdf`, `bin_model`) | … |
| 04 | DESULMA Johnsley | Orchestration ROS 2 | Machine à états centrale, prévention des collisions | `fsm.py`, `orchestrator_node.py`, `collision.py`, `launch/` | … |
| 05 | DIEUYEL Jean Jeudy | Perception / IA | Module de classification (attributs ou OpenCV) | `classifier.py`, `perception_node.py`, `test/test_classifier.py` | … |
| 06 | JANVIER John Clarence A. | Configuration Robot B | Modèle SDF du bras B chargé dans Gazebo | `simulation/models/robot_arm_b/`, `kinematics.py` (dimensions) | … |
| 07 | LUMERANT Laïsha M. | Tests & Soutenance | Rapport de 10 cycles, vidéo 3-5 min, slides PDF | `tests/`, `docs/PLAN_DE_TESTS.md`, `presentation/`, `video/` | … |
| 08 | NOËL Françoise | Convoyeur & Objets | Convoyeur animé, génération d'objets colorés | `world_model.py`, `conveyor_node.py`, `piece_model.py` | … |
| 09 | REMY Emmanuel | Configuration Robot A | Modèle SDF du bras A chargé dans Gazebo | `simulation/models/robot_arm_a/`, `kinematics.py` (IK/FK) | … |
| 10 | SAINT-PRÉVIL Stecy Carla | Coordination & Git | Dépôt GitHub, planning, Pull Requests | `.github/`, `docs/GITFLOW_ET_PLANNING.md`, `README.md` | … |
| 11 | *(à confirmer — Poste A)* | Installation & Config | Guide d'installation Ubuntu/ROS 2/Gazebo | `scripts/install_ubuntu_ros2_gazebo.sh`, `scripts/build.sh`, `docs/INSTALLATION.md` | … |
| 12 | *(à confirmer — Poste B)* | Supervision & Data | Logs, métriques, dashboard de suivi | `metrics.py`, `supervision_node.py`, `dashboard.py` | … |


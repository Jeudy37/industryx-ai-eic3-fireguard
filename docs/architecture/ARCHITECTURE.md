# Architecture

## 1. Principe : « modules purs » + « nœuds fins »
Toute la logique (cinématique, trajectoires, machine à états, monde, classification, métriques) est dans des modules Python **sans dépendance ROS**.
Les nœuds `*_node.py` ne font que recevoir/publier des messages. Conséquences : tests unitaires rapides, intégration continue sans ROS,
et une simulation logique (`headless_sim.py`) qui exécute **les mêmes classes** que les nœuds.

| Module pur | Rôle | Nœud ROS 2 |
|---|---|---|
| `config.py` | Géométrie, points de passage, règle de tri (source unique, lue aussi par le générateur SDF) | — |
| `kinematics.py` | IK analytique / FK du bras 4 axes, limites articulaires | — |
| `motion.py` | Trajectoires « minimum jerk », exécuteur de plan | — |
| `robot_controller.py` | Primitives PICK/PLACE/HOME, validation IK, états IDLE/BUSY/ERROR | `robot_a_node`, `robot_b_node` |
| `world_model.py` | Convoyeur, file d'attente, génération, préhension simulée, pannes injectées | `conveyor_node` |
| `fsm.py` | Orchestrateur : pipeline, verrou zone T, reprises, timeouts | `orchestrator_node` |
| `classifier.py` | Règle par attributs + OpenCV (HSV, contours) | `perception_node` |
| `metrics.py`, `collision.py` | Journal/CSV/JSON, distance « capsules » entre bras | `supervision_node` |

## 2. Topics (messages JSON dans `std_msgs/String` — pas de paquet de messages à compiler)
| Topic | Type | Émetteur → récepteurs | Contenu |
|---|---|---|---|
| `/world/events` | String(JSON) | conveyor → orchestrator, perception, supervision | `spawned`, `ready`, `grasped`, `grasp_failed`, `transferred`, `binned`, `dropped`, `removed` |
| `/robot_x/command` | String(JSON) | orchestrator → robot | `{cmd_id, cmd, piece_id, bin, pos}` |
| `/robot_x/status` | String(JSON) | robot → orchestrator, supervision | `{state, task, cmd_id, last_done, zone, holding, error}` (10 Hz) |
| `/robot_x/tool_pose` | PointStamped | robot → conveyor | position du TCP (50 Hz) |
| `/robot_x/gripper` | String(JSON) | robot → conveyor | `{closed, piece_id}` |
| `/robot_x/joint_cmd` | JointState | robot → supervision | consignes articulaires (sécurité) |
| `/robot_x/jN/cmd` | Float64 | robot → Gazebo (pont) | consigne de position de l'axe N |
| `/perception/classification` | String(JSON) | perception → orchestrator | `{piece, color, shape, bin, confidence, method}` |
| `/orchestrator/log` | String(JSON) | orchestrator → supervision | décisions de la FSM |
| `/supervision/metrics`, `/supervision/alerts` | String(JSON) | supervision | résumé 1 Hz, alertes de proximité |
| `/camera/image` | Image | Gazebo → perception | caméra zénithale 320×240 |

## 3. Machine à états et coordination
**Verrou de la zone de transfert T** (le cœur de la prévention de collisions) :
- A ne peut lancer `PLACE_TRANSFER` que si T est vide **et** le verrou est libre ; B ne peut lancer `PICK_TRANSFER` que si une pièce attend **et** le verrou est libre.
- Le verrou est libéré lorsque le propriétaire n'exécute plus la commande d'entrée **et** que son TCP a quitté le disque de rayon 0,30 m autour de T.
- Hors de T, les bras travaillent en parallèle : leurs espaces de travail ne se recouvrent pas (cf. implantation).

**Trois couches de sécurité** : (1) IK + limites articulaires vérifiées **avant** tout mouvement (cible refusée → `ERROR`) ;
(2) verrou exclusif de T ; (3) surveillance continue de la distance minimale entre capsules (rayon 4 cm) dans `supervision_node` — alerte < 0,11 m, collision < 0,08 m.

**Robustesse** : échec de préhension → retour `HOME` puis nouvel essai (3 max) puis rebut de la pièce ; timeout de commande (45 s) → défaut, `HOME`, verrou libéré ;
classification absente (6 s) → bac C par défaut, journalisé ; caméra muette → repli sur la règle par attributs.

## 4. Cinématique du bras
Tourelle (lacet) + épaule + coude + poignet ; L1 = L2 = 0,30 m, hauteur d'épaule 0,15 m, préhenseur 0,10 m, portée utile ≈ 0,6 m. Outil toujours vertical.
IK analytique (coude en haut) ; trajectoire articulaire « minimum jerk » (vitesse/accélération nulles aux extrémités).
Position articulaire 0 = bras vertical → aucune collision possible quand Gazebo démarre.

## 5. Simulation Gazebo
- `simulation/worlds/industry_x.world` : généré par `generate_simulation.py` depuis `config.py` (sol, table, convoyeur, plaque de transfert, 3 bacs, caméra, 2 bras).
- Bras : modèles SDF `robot_arm_a/b`, 4 × `JointPositionController` (consigne `/robot_x/jN/cmd`).
- Pièces : créées à la volée (service `create`), poses pilotées par `set_pose` (pont ROS ↔ Gazebo, repli `gz service`).

# Tests — journaux et métriques

| Fichier | Origine | Contenu |
|---|---|---|
| `JOURNAL_10_CYCLES.md` | section A : généré par `headless_sim` ; **section B : à remplir avec le run Gazebo** | tableau des 10 cycles + métriques |
| `logs/headless_nominal.csv/.json` | `headless_sim` (logique, sans Gazebo) | 10 cycles nominaux |
| `logs/headless_robustesse_pannes.csv/.json` | idem, 25 % de pannes de préhension injectées (graine 3) | reprises et récupération |
| `logs/headless_aleatoire.csv/.json` | idem, 12 pièces aléatoires (graine 7) | tri multi-catégories |
| `logs/gazebo_run_XX.csv/.json` | **à ajouter** : `cp ~/industry_x_logs/run_*.csv tests/logs/gazebo_run_01.csv` | run Gazebo réel |

Les tests unitaires sont dans `src/industry_x_ai/test/` (convention ROS 2) ; voir `docs/PLAN_DE_TESTS.md`.
Colonnes du CSV : `cycle, piece_id, color, shape, expected_bin, sorted_bin, result, t_spawn, t_ready, t_grasp_A, t_transfer, t_grasp_B, t_binned, cycle_time_s, total_time_s, retries, classif_method, min_arm_dist_m`.

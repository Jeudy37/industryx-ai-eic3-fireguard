# Journal de 10 cycles

## A. Validation de la logique (simulation « sans tête », `headless_sim`) — reproductible

> Généré par `bash scripts/run_tests.sh` (mêmes classes que les nœuds ROS 2, temps simulé, **sans Gazebo**).
> Il prouve la logique de coordination ; il ne remplace pas la section B.

### A.1 Run nominal — 10 pièces (`tests/logs/headless_nominal.csv`)
| # | Pièce | Couleur | Forme | Bac attendu | Bac obtenu | Résultat | Temps de cycle (s) | Reprises | Méthode |
|---|---|---|---|---|---|---|---|---|---|
| 1 | piece_1 | red | cube | A | A | OK | 12.88 | 0 | attributs |
| 2 | piece_2 | green | cylinder | B | B | OK | 14.9 | 0 | attributs |
| 3 | piece_3 | blue | cube | C | C | OK | 17.2 | 0 | attributs |
| 4 | piece_4 | red | cylinder | A | A | OK | 16.78 | 0 | attributs |
| 5 | piece_5 | green | cube | B | B | OK | 18.82 | 0 | attributs |
| 6 | piece_6 | blue | cylinder | C | C | OK | 21.2 | 0 | attributs |
| 7 | piece_7 | red | cube | A | A | OK | 20.82 | 0 | attributs |
| 8 | piece_8 | green | cylinder | B | B | OK | 21.86 | 0 | attributs |
| 9 | piece_9 | blue | cube | C | C | OK | 22.56 | 0 | attributs |
| 10 | piece_10 | red | cylinder | A | A | OK | 20.94 | 0 | attributs |

| Métrique | Valeur |
|---|---|
| Pièces traitées / réussies | 10 / 10 (100.0 %) |
| Répartition par bac | A = 4, B = 3, C = 3 |
| Collisions | **0** |
| Distance minimale entre les bras | 0.251 m (seuil d'alerte 0,11 m ; contact 0,08 m) |
| Temps de cycle moyen / min / max | 18.8 / 12.88 / 22.56 s |
| Débit | 5.51 pièces/min |

### A.2 Test de robustesse — 25 % d'échecs de préhension injectés (`headless_robustesse_pannes.csv`)
| # | Pièce | Couleur | Forme | Bac attendu | Bac obtenu | Résultat | Temps de cycle (s) | Reprises | Méthode |
|---|---|---|---|---|---|---|---|---|---|
| 1 | piece_1 | red | cube | A | A | OK | 16.72 | 1 | attributs |
| 2 | piece_2 | green | cylinder | B | B | OK | 30.56 | 2 | attributs |
| 3 | piece_3 | blue | cube | C | C | OK | 38.8 | 1 | attributs |
| 4 | piece_4 | red | cylinder | A | A | OK | 38.46 | 0 | attributs |
| 5 | piece_5 | green | cube | B | B | OK | 27.76 | 0 | attributs |
| 6 | piece_6 | blue | cylinder | C | C | OK | 22.56 | 0 | attributs |
| 7 | piece_7 | red | cube | A | A | OK | 22.86 | 1 | attributs |
| 8 | piece_8 | green | cylinder | B | B | OK | 25.7 | 1 | attributs |
| 9 | piece_9 | blue | cube | C | C | OK | 28.2 | 0 | attributs |
| 10 | piece_10 | red | cylinder | A | A | OK | 32.68 | 1 | attributs |

Reprises totales : **7** ; pièces traitées : 10/10 ; réussies : 10 ; abandonnées : 0 ; collisions : **0** ; défauts : 0.
Les échecs de préhension déclenchent un retour `HOME` puis une nouvelle tentative (3 maximum), sans blocage ni collision.

## B. Run Gazebo réel — À COMPLÉTER PAR L'ÉQUIPE (étudiante 07)

1. Lancer `bash scripts/run_simulation.sh`, laisser passer les 10 pièces, copier `~/industry_x_logs/run_*.csv` vers `tests/logs/gazebo_run_01.csv`.
2. Coller ici le tableau (`CycleLogger.markdown_table()` ou le CSV) et les métriques du dashboard :

| Métrique | Valeur Gazebo |
|---|---|
| Date / machine / facteur temps réel | … |
| Pièces traitées / réussies | … / … |
| Collisions · distance min. | … · … m |
| Temps de cycle moyen | … s |
| Observations (réglages effectués) | … |

3. Joindre les captures `docs/captures/07_dashboard.png` et `09_resultat_10_cycles.png`.

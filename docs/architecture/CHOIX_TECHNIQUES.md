# Choix techniques, justifications et limites assumées

| Choix | Justification | Limite / évolution |
|---|---|---|
| **Bras 4 axes simples en SDF**, créés pour le projet | Géométrie maîtrisée (IK analytique exacte, tests), aucune dépendance à un paquet externe, chargement garanti ; le cahier des charges autorise « modèle URDF/SDF ». | Moins réaliste qu'un UR5/Panda. Évolution : remplacer par `ur_description` + MoveIt 2. |
| **Pas de MoveIt 2** (marqué « Recommandé / Optionnel MVP ») | Trajectoires déterministes par IK analytique + interpolation « minimum jerk » ; collisions évitées par construction (verrou) et surveillées (capsules). | Pas d'évitement d'obstacles généraux : l'environnement est fixe et connu. |
| **Préhension par attachement cinématique** (la pièce suit le TCP) | Fiable et reproductible ; évite le réglage fin de frottements/contacts d'un préhenseur physique, source classique d'échecs en démonstration. | Pas de physique de contact. Évolution : plugin `DetachableJoint` ou préhenseur à deux doigts. |
| **Pièces sans gravité ni collision, poses pilotées** | Comportement déterministe (pas de rebond, de glissement ni de chute). | Convoyeur « logique » (le tapis ne frotte pas la pièce). |
| **Bras sans gravité, commandés en position** | Maintien de pose garanti sans réglage PID fin. | Dynamique simplifiée. |
| **Messages JSON dans `std_msgs/String`** | Aucun paquet de messages personnalisé à compiler → build plus simple et robuste pour 12 étudiants. | Moins typé ; évolution : `industry_x_interfaces` (msg/srv/action). |
| **Orchestrateur = classe Python pure** | Testable sans ROS, déterministe, rejouable (journal). | — |
| **Temps simulé (`/clock`)** | Cohérence avec le facteur temps réel de Gazebo. | — |
| **Tri par couleur, forme journalisée** | 3 bacs ↔ 3 couleurs ; la forme est détectée (OpenCV) et enregistrée pour extension (règle de tri configurable dans `config.BIN_RULE`). | — |
| **Deux méthodes de classification** (attributs / OpenCV) | Le cahier des charges demande de comparer IA et règle classique ; mode `compare`. | OpenCV sans apprentissage (seuils HSV) : suffisant pour des couleurs franches. |

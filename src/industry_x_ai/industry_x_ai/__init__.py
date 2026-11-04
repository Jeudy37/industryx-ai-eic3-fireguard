"""INDUSTRY-X AI — cellule de tri robotisée (EIC 3.0, équipe FIREGUARD-X).

Les modules « purs » (config, kinematics, collision, motion, robot_controller,
world_model, fsm, classifier, metrics, headless_sim) n'importent PAS rclpy :
ils sont testables sans ROS 2. Les fichiers ``*_node.py`` ne font que
l'entrée/sortie ROS 2 autour de cette logique.
"""
__version__ = "1.0.0"

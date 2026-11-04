"""Point d'entrée du robot A (préhension). Voir robot_node.py."""
from .robot_node import run


def main(args=None):
    run("A", args)

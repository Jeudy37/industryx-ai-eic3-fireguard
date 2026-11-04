#!/usr/bin/env bash
# Compile le paquet ROS 2 (mode --symlink-install : le lancement retrouve simulation/ tout seul).
set -euo pipefail
cd "$(dirname "$0")/.."
source /opt/ros/jazzy/setup.bash
python3 simulation/tools/generate_simulation.py          # régénère le monde SDF depuis config.py
colcon build --symlink-install --packages-select industry_x_ai
echo "✅ Build OK.  Lancer :  bash scripts/run_simulation.sh"

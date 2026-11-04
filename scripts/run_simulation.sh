#!/usr/bin/env bash
# Lance la simulation complète. Arguments supplémentaires = arguments de launch, ex. :
#   bash scripts/run_simulation.sh perception_mode:=opencv
#   bash scripts/run_simulation.sh headless:=true total_pieces:=10
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
source "$ROOT/install/setup.bash"
export INDUSTRY_X_SIM_DIR="$ROOT/simulation"
exec ros2 launch industry_x_ai simulation.launch.py "$@"

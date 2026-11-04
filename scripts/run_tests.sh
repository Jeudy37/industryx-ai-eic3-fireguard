#!/usr/bin/env bash
# Tests unitaires + tests de robustesse (sans ROS ni Gazebo) puis régénération des journaux headless.
set -euo pipefail
cd "$(dirname "$0")/../src/industry_x_ai"
python3 -m pytest -v test
cd ../..
PYTHONPATH=src/industry_x_ai python3 -m industry_x_ai.headless_sim --pieces 10 --out tests/logs --tag headless_nominal
PYTHONPATH=src/industry_x_ai python3 -m industry_x_ai.headless_sim --pieces 10 --fail-rate 0.25 --seed 3 --out tests/logs --tag headless_robustesse_pannes
PYTHONPATH=src/industry_x_ai python3 -m industry_x_ai.headless_sim --pieces 12 --random --seed 7 --out tests/logs --tag headless_aleatoire

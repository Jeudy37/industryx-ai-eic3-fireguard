#!/usr/bin/env bash
# Construit le dossier INDUSTRY_X_AI_GROUPE_12/ (structure 01..06 du cahier des charges) depuis le dépôt.
set -euo pipefail
cd "$(dirname "$0")/.."
D=INDUSTRY_X_AI_GROUPE_12
rm -rf $D && mkdir -p $D/{01_CODE,02_SIMULATION,03_DOCUMENTATION,04_CAPTURES,05_VIDEO,06_EQUIPE}
cp -r src $D/01_CODE/ ; cp -r scripts $D/01_CODE/
cp -r simulation $D/02_SIMULATION/
cp README.md docs/*.md $D/03_DOCUMENTATION/ ; cp -r docs/architecture $D/03_DOCUMENTATION/
cp -r tests $D/03_DOCUMENTATION/tests ; cp presentation/*.pdf $D/03_DOCUMENTATION/ 2>/dev/null || true
cp -r docs/captures/* $D/04_CAPTURES/ 2>/dev/null || true
cp video/* $D/05_VIDEO/ ; cp CONTRIBUTIONS.md $D/06_EQUIPE/
echo "✅ $D créé"

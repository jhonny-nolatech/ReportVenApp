#!/usr/bin/env bash
# Un solo comando: prepara el entorno y genera un informe en Word.
#
#   bash scripts/generar.sh                              # GENERAL (situacional nacional)
#   bash scripts/generar.sh -t operativo_zonas_criticas  # ENFOCADO (La Guaira + Miranda/Chacao)
#   bash scripts/generar.sh -t puntos_ciegos             # reporte de zonas silenciosas
#   bash scripts/generar.sh -t resumen_ejecutivo -m claude-opus-4-8
#
# Requiere: .env con ANTHROPIC_API_KEY y una fuente de datos (VPN a Mongo o
# un report_*.xlsx en la raíz del proyecto).
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "❌ Falta el archivo .env. Copia .env.example a .env y rellena ANTHROPIC_API_KEY."
  echo "   cp .env.example .env"
  exit 1
fi

python3 -m venv .venv 2>/dev/null || true
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt
python scripts/generar.py "$@"

"""Genera la Alerta de Salud Pública y Riesgo de Epidemias (.docx).

Cruza población desplazada (hacinamiento) + reportes de agua/saneamiento (riesgo
diarreico/cólera) + agua estancada/basura (dengue) en un índice de riesgo sanitario
por estado, con brechas WASH (Esfera) y acciones preventivas. No usa IA.

Uso:
    python scripts/generar_salud_publica.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.report.reporte_salud_publica import generar_reporte  # noqa: E402


def main() -> int:
    print("⏳ Analizando riesgo sanitario (desplazados × agua/saneamiento × vectores)…")
    ruta = generar_reporte()
    print(f"✅ Reporte generado: {ruta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

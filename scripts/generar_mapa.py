"""Genera el Mapa Operacional interactivo (HTML/Leaflet) por parroquia.

Uso:
    python scripts/generar_mapa.py

Salida: reports_out/mapa_operacional.html — se abre en cualquier navegador (sin
servidor). Datos agregados por parroquia (sin PII). Requiere la clasificación por IA
ya corrida (scripts/clasificar_edificios.py).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.report.mapa_operacional import generar_mapa_html  # noqa: E402


def main() -> int:
    print("⏳ Generando mapa operacional…")
    ruta = generar_mapa_html()
    print(f"✅ Mapa generado: {ruta}")
    print("   Ábrelo en el navegador (doble clic). Cada parroquia es un marcador con popup.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

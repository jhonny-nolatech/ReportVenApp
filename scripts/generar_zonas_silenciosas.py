"""Genera el reporte de Zonas Silenciosas / Puntos Ciegos (.docx).

Cruza intensidad sísmica × población × reportes recibidos para detectar dónde hay
probable daño del que NO nos estamos enterando (comunicaciones/acceso cortados).
Determinista — no usa IA ni consume tokens.

Uso:
    python scripts/generar_zonas_silenciosas.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.report.reporte_zonas_silenciosas import generar_reporte  # noqa: E402


def main() -> int:
    print("⏳ Analizando zonas silenciosas (MMI × población × reportes)…")
    ruta = generar_reporte()
    print(f"✅ Reporte generado: {ruta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

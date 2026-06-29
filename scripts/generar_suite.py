"""Genera, en un solo comando, el informe base + los 3 informes derivados.

Uso:
    python scripts/generar_suite.py                         # nacional, modelo por defecto
    python scripts/generar_suite.py -e "La Guaira"          # con foco geográfico
    python scripts/generar_suite.py -m claude-opus-4-8 -i "Enfócate en el eje Carabobo"

Produce en reports_out/:
    INFORME_BASE.docx, INFORME_TECNICO_OPERATIVO.docx (con gráficos),
    BRIEF_PRESIDENCIAL.docx, PLAN_DE_COMUNICACION_DE_EMERGENCIA.docx
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent.suite import generar_suite  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Suite de informes (base + 3 derivados).")
    p.add_argument("-e", "--estado", default=None, help="Estado/provincia (opcional).")
    p.add_argument("-i", "--instruccion", default="", help="Instrucción adicional (opcional).")
    p.add_argument("-m", "--modelo", default=None, help="Modelo Anthropic (opcional).")
    p.add_argument("-o", "--salida", default=None, help="Directorio de salida (opcional).")
    args = p.parse_args()

    print("⏳ Generando suite de informes (base + técnico + brief + comunicación)…")
    print("   Esto consume tokens de Anthropic y consulta la BD (solo lectura).")
    salidas = generar_suite(args.estado, args.instruccion, args.modelo, args.salida)

    print("\n✅ Suite generada:")
    for clave, ruta in salidas.items():
        print(f"   - {clave:32} -> {ruta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Generador de informes por línea de comandos.

Uso:
    python scripts/generar.py                         # GENERAL: situacional estratégico (nacional)
    python scripts/generar.py -t operativo_zonas_criticas   # ENFOCADO: La Guaira + Miranda/Chacao
    python scripts/generar.py -t resumen_ejecutivo
    python scripts/generar.py -t puntos_ciegos
    python scripts/generar.py -t foco_geografico -e "La Guaira"
    python scripts/generar.py -t situacional_estrategico -m claude-opus-4-8 -i "Enfócate en Caracas"

Tipos disponibles: situacional_estrategico (general), operativo_zonas_criticas (enfocado
La Guaira+Miranda/Chacao), resumen_ejecutivo, foco_desaparecidos, foco_dano_estructural,
foco_geografico, puntos_ciegos.

Fuente de datos: usa la BD de VenApp si hay VPN; si no, cae automáticamente al
Excel de respaldo (report_*.xlsx en la raíz o $VENAPP_EXCEL_PATH).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent.orchestrator import generar_informe_dict  # noqa: E402
from app.agent.schema import TIPOS_REPORTE  # noqa: E402
from app.report.docx_renderer import render_informe  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Genera un informe estratégico en Word.")
    p.add_argument("-t", "--tipo", default="situacional_estrategico",
                   choices=list(TIPOS_REPORTE.keys()), help="Tipo de informe.")
    p.add_argument("-e", "--estado", default=None, help="Estado/provincia (opcional).")
    p.add_argument("-i", "--instruccion", default="", help="Instrucción adicional (opcional).")
    p.add_argument("-m", "--modelo", default=None,
                   help="Modelo Anthropic (claude-sonnet-4-6 por defecto, claude-opus-4-8 más exhaustivo).")
    p.add_argument("-o", "--salida", default=None, help="Ruta .docx de salida (opcional).")
    args = p.parse_args()

    print(f"⏳ Generando informe '{args.tipo}'"
          + (f" para {args.estado}" if args.estado else " (nacional)") + "…")
    print("   (consultando datos, riesgos, puntos ciegos, casos análogos y protocolos)")

    informe = generar_informe_dict(args.tipo, args.estado, args.instruccion, args.modelo)
    path = render_informe(informe, args.salida)

    print("\n✅ Informe generado:")
    print("   Archivo :", path)
    print("   Resumen :", (informe.get("resumen_ejecutivo") or "")[:160], "…")
    print("   Riesgos :", len(informe.get("analisis_riesgos", [])),
          "| Recomendaciones:", len(informe.get("recomendaciones", [])),
          "| Zonas ciegas:", len(informe.get("zonas_ciegas", [])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

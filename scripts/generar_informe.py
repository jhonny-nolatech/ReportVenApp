"""Genera el Brief Presidencial y/o el Informe Técnico-Operativo.

Cada documento se guarda con un nombre de archivo igual a su título.

Uso:
    python scripts/generar_informe.py                 # AMBOS (brief + técnico)
    python scripts/generar_informe.py -t brief        # solo el Brief Presidencial
    python scripts/generar_informe.py -t tecnico      # solo el Informe Técnico-Operativo
    python scripts/generar_informe.py -t ambos        # ambos (igual que sin -t)
    python scripts/generar_informe.py -t albergues    # solo el Plan de albergues/desplazados
    python scripts/generar_informe.py -t todos        # los 4 derivados (+ comunicación + albergues)

Por defecto, CADA corrida recalcula TODOS los datos y métricas desde la BD en
vivo (la BD se actualiza constantemente, así que cada informe trae datos nuevos).

Opciones:
    -e "La Guaira"   foco geográfico (opcional)
    -m claude-opus-4-8   modelo más exhaustivo (opcional)
    --reusar-base    (avanzado) reusa el informe base cacheado en vez de
                     recalcularlo — solo para generar varios documentos seguidos
                     más rápido sobre el MISMO corte. NO usar si quieres datos
                     frescos.

Salida en reports_out/:
    "Evaluación de daños y respuesta inmediata - Terremoto 24J.docx"
    "Balance de daños y operaciones de campo posterior al Terremoto del 24J.docx"
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent.suite import generar_suite  # noqa: E402

_GRUPOS = {
    "brief": ["brief"],
    "tecnico": ["tecnico"],
    "comunicacion": ["comunicacion"],
    "albergues": ["albergues"],
    "ambos": ["brief", "tecnico"],
    "todos": ["brief", "tecnico", "comunicacion", "albergues"],
}


def main() -> int:
    p = argparse.ArgumentParser(description="Genera el Brief Presidencial y/o el Informe Técnico-Operativo.")
    p.add_argument("-t", "--tipo", default="ambos", choices=list(_GRUPOS.keys()),
                   help="Qué generar: brief, tecnico, ambos (def.), comunicacion, albergues o todos.")
    p.add_argument("-e", "--estado", default=None, help="Estado/provincia (opcional).")
    p.add_argument("-i", "--instruccion", default="", help="Instrucción adicional (opcional).")
    p.add_argument("-m", "--modelo", default=None, help="Modelo Anthropic (opcional).")
    p.add_argument("-o", "--salida", default=None, help="Directorio de salida (opcional).")
    p.add_argument("--reusar-base", dest="reusar_base", action="store_true",
                   help="(avanzado) reusa el informe base cacheado en vez de recalcular. "
                        "Por defecto SIEMPRE se recalculan todos los datos en vivo.")
    args = p.parse_args()

    reportes = _GRUPOS[args.tipo]
    print(f"⏳ Generando: {', '.join(reportes)}"
          + (f" (foco {args.estado})" if args.estado else "")
          + (" · reusando base cacheado" if args.reusar_base else " · datos FRESCOS (recalcula todo)") + "…")
    print("   Consume tokens de Anthropic y consulta la BD/Excel (solo lectura).")

    salidas = generar_suite(
        estado=args.estado, instruccion=args.instruccion, modelo=args.modelo,
        outdir=args.salida, solo=reportes, reusar_base=args.reusar_base,
        incluir_base=False,
    )

    print("\n✅ Documentos generados:")
    for clave, ruta in salidas.items():
        print(f"   - {clave:14} -> {ruta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

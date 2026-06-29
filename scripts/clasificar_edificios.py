"""Clasifica con IA los reportes del Terremoto 24J en edificios derrumbados / en
riesgo de colapso, extrayendo el ESTADO REAL del hecho (corrige el sesgo de
"denunciado desde Caracas"). Cacheado e incremental: reejecutar solo clasifica lo
nuevo, así que es seguro pararlo y retomarlo.

Uso:
    python scripts/clasificar_edificios.py                 # clasifica TODO (incremental)
    python scripts/clasificar_edificios.py -n 200          # solo los primeros 200 (prueba)
    python scripts/clasificar_edificios.py --refrescar     # ignora el caché y reclasifica
    python scripts/clasificar_edificios.py --aptos 80 --personas 5   # supuestos del resumen

Consume tokens de Anthropic (modelo barato Haiku por defecto). Las cifras de
edificios alimentan luego el "Plan de albergues" (estimación corregida del sesgo).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.tools import clasificador_edificios as ce  # noqa: E402


def _fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def main() -> int:
    p = argparse.ArgumentParser(description="Clasifica reportes en edificios derrumbados/en riesgo (IA).")
    p.add_argument("-n", "--limite", type=int, default=None, help="Clasificar solo los primeros N (prueba).")
    p.add_argument("-m", "--modelo", default=None, help="Modelo Anthropic (def.: Haiku).")
    p.add_argument("--refrescar", action="store_true", help="Ignora el caché y reclasifica todo.")
    p.add_argument("--aptos", type=int, default=100, help="Apartamentos promedio por edificio (resumen).")
    p.add_argument("--personas", type=int, default=6, help="Personas por hogar (resumen).")
    args = p.parse_args()

    print("⏳ Clasificando reportes con IA (esto consume tokens de Anthropic)…")
    cache = ce.clasificar(modelo=args.modelo, limite=args.limite, refrescar=args.refrescar)

    res = ce.resumen(aptos_promedio=args.aptos, personas_hogar=args.personas, cache=cache)
    print(f"\n✅ Clasificados: {_fmt(res['clasificados'])} reportes")
    print(f"   Edificios DERRUMBADOS (distintos): {_fmt(res['total_edificios_derrumbados'])}")
    print(f"   Edificios EN RIESGO   (distintos): {_fmt(res['total_edificios_riesgo'])}")
    print(f"   Total a REUBICAR  ({args.aptos} aptos × {args.personas} pers): {_fmt(res['total_a_reubicar'])} personas")
    print(f"   Próximos a reubicar (en riesgo):     {_fmt(res['total_proximos_reubicar'])} personas")
    print("\n   Top estados (por personas a reubicar):")
    for f in res["por_estado"][:10]:
        print(f"     {f['estado']:14} derrumbados={f['edificios_derrumbados']:4} "
              f"riesgo={f['edificios_riesgo']:4}  a_reubicar={_fmt(f['personas_a_reubicar'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

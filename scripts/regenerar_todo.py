"""Regenera TODOS los entregables tras recibir un CSV actualizado — en un comando.

Flujo (en orden):
  1. Clasifica los reportes con IA (INCREMENTAL: solo clasifica los reportes nuevos;
     usa --refrescar para reclasificar todo desde cero).
  2. Informes situacionales: brief, técnico-operativo, comunicación y albergues.
  3. Reporte de zonas silenciosas / puntos ciegos.
  4. Reporte de alerta de salud pública / epidemias.
  5. Mapa operacional interactivo (HTML).
  6. CSV combinado (reportes + clasificación).
  7. (Opcional) Publica el mapa en su enlace público — si GH_TOKEN está definido.

Requisitos:
  - Coloca el CSV nuevo (terremoto*.csv) en la raíz del proyecto (se toma el más reciente).
  - Para publicar el mapa: exporta GH_TOKEN=<token de GitHub>.

Uso:
    python scripts/regenerar_todo.py                # todo (clasificación incremental)
    python scripts/regenerar_todo.py --refrescar     # reclasifica TODO desde cero
    python scripts/regenerar_todo.py --sin-informes  # omite los informes LLM (más rápido/barato)
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PY = sys.executable  # el mismo intérprete (venv) con el que se lanza


def _run(desc: str, args: list[str]) -> bool:
    print(f"\n{'='*70}\n▶ {desc}\n{'='*70}")
    t0 = time.time()
    r = subprocess.run([PY, str(RAIZ / "scripts" / args[0]), *args[1:]], cwd=str(RAIZ))
    ok = r.returncode == 0
    print(f"{'✅' if ok else '❌'} {desc}  ({time.time()-t0:.0f}s)")
    return ok


def main() -> int:
    p = argparse.ArgumentParser(description="Regenera todos los entregables.")
    p.add_argument("--refrescar", action="store_true", help="Reclasifica TODOS los reportes (no incremental).")
    p.add_argument("--sin-informes", action="store_true", help="Omite los informes LLM (brief/técnico/etc.).")
    p.add_argument("--sin-clasificar", action="store_true", help="No corre la clasificación IA (usa la cacheada).")
    args = p.parse_args()

    pasos: list[tuple[str, list[str]]] = []
    if not args.sin_clasificar:
        clas = ["clasificar_edificios.py"] + (["--refrescar"] if args.refrescar else [])
        pasos.append(("1. Clasificación por IA (edificios derrumbados / en riesgo)", clas))
    if not args.sin_informes:
        pasos.append(("2. Informes: brief, técnico, comunicación y albergues", ["generar_informe.py", "-t", "todos"]))
    pasos += [
        ("3. Zonas silenciosas / puntos ciegos", ["generar_zonas_silenciosas.py"]),
        ("4. Alerta de salud pública / epidemias", ["generar_salud_publica.py"]),
        ("5. Termómetro de necesidades emergentes", ["generar_necesidades.py"]),
        ("6. Mapa operacional interactivo (HTML)", ["generar_mapa.py"]),
        ("7. CSV combinado (reportes + clasificación)", ["exportar_clasificacion.py"]),
    ]
    if os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"):
        pasos.append(("7. Publicar el mapa en su enlace público", ["publicar_mapa.py"]))
    else:
        print("ℹ️  (Se omite la publicación del mapa: define GH_TOKEN para publicarlo.)")

    print(f"🚀 Regenerando {len(pasos)} pasos…")
    resultados = [(desc, _run(desc, a)) for desc, a in pasos]

    print(f"\n{'='*70}\nRESUMEN")
    for desc, ok in resultados:
        print(f"  {'✅' if ok else '❌'} {desc}")
    fallos = [d for d, ok in resultados if not ok]
    print(f"\n{'🎉 Todo listo.' if not fallos else '⚠️ Con fallos: ' + '; '.join(fallos)}")
    print("   Documentos en: reports_out/")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())

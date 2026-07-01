"""Migra la clasificación de ayer al export nuevo, por MATCH DE CONTENIDO.

El export nuevo cambió el formato del número de reporte, así que el caché por ID no
sirve. Pero el mismo reporte tiene el mismo título + descripción + coordenadas. Este
script empareja por contenido y RE-SIEMBRA el caché con la clasificación ya hecha,
para NO reclasificar los ~15 mil que ya procesamos (solo quedarán los nuevos).

Fuente: reports_out/reportes_clasificados.csv (combinado generado ayer).
Salida: cache_clasificacion_edificios.json (re-sembrado).

Uso:
    python scripts/migrar_clasificacion.py
    # luego:  python scripts/clasificar_edificios.py   (clasifica SOLO los nuevos)
"""
import csv
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.mongo import build_event_query, get_reports_collection  # noqa: E402
from app.tools import clasificador_edificios as ce  # noqa: E402

COMBINADO = "reports_out/reportes_clasificados.csv"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]", " ", (s or "").lower())).strip()


def _key(titulo, desc, lat, lng) -> str:
    c = ""
    try:
        c = f"{round(float(lat), 4)},{round(float(lng), 4)}"
    except (TypeError, ValueError):
        pass
    return f"{_norm(titulo)}§{_norm(desc)}§{c}"


def main() -> int:
    if not os.path.exists(COMBINADO):
        print(f"❌ No existe {COMBINADO} (el combinado de ayer). No hay de dónde migrar.")
        return 1

    # 1) Mapa contenido -> clasificación (del combinado de ayer).
    viejo: dict[str, dict] = {}
    with open(COMBINADO, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            tipo = (r.get("clas_tipo") or "").strip()
            if tipo not in ("derrumbado", "riesgo", "vivienda", "otro"):
                continue
            viejo[_key(r.get("Titulo"), r.get("Descripcion"), r.get("Latitud"), r.get("Longitud"))] = {
                "tipo": tipo,
                "vertical": (r.get("clas_vertical") or "").strip().lower() == "si",
                "estado_real": (r.get("clas_estado_real") or "").strip() or None,
            }
    print(f"Clasificaciones de ayer disponibles: {len(viejo)}")

    # 2) Recorre los reportes nuevos; re-siembra el caché por su NÚMERO nuevo.
    col = get_reports_collection()
    cache: dict[str, dict] = {}
    total = migrados = 0
    for d in col.find(build_event_query()):
        total += 1
        num = d.get("number")
        if not num:
            continue
        k = _key(d.get("title"), d.get("description"), d.get("latitude"), d.get("longitude"))
        c = viejo.get(k)
        if not c:
            continue
        migrados += 1
        prov = (d.get("province") or {}).get("name") if isinstance(d.get("province"), dict) else None
        cache[num] = {**c, "estado_decl": prov,
                      "lat": d.get("latitude"), "lng": d.get("longitude")}

    # 3) Guarda el caché re-sembrado.
    with open(ce.CACHE_PATH, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, ensure_ascii=False)

    print(f"✅ Migración lista.")
    print(f"   Reportes nuevos: {total}")
    print(f"   Reusados de ayer (match por contenido): {migrados}")
    print(f"   Faltan por clasificar: {total - migrados}")
    print("\n   Ahora corre:  python scripts/clasificar_edificios.py")
    print("   (clasificará SOLO los nuevos; los demás ya están.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

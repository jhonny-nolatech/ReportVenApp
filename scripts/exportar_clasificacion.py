"""Une cada reporte (CSV original) con su clasificación por IA y exporta un CSV
combinado: columnas originales + clas_tipo / clas_vertical / clas_estado_real.

Salida: reports_out/reportes_clasificados.csv  (carpeta gitignored).
ATENCIÓN: contiene PII (cédula/teléfono/email) igual que el export original.
NO versionar ni compartir externamente.

Uso:
    python scripts/exportar_clasificacion.py
"""
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.excel_source import excel_path           # noqa: E402
from app.tools import clasificador_edificios as ce    # noqa: E402
from app.config import Settings                        # noqa: E402


def main() -> int:
    src = excel_path()
    if not src or not src.lower().endswith(".csv"):
        print(f"❌ No encuentro el CSV de reportes (excel_path={src}).")
        return 1
    cache = ce._cargar_cache()
    if not cache:
        print("❌ No hay clasificación cacheada. Corre antes: python scripts/clasificar_edificios.py")
        return 1

    out_dir = Settings().reports_out_dir
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "reportes_clasificados.csv")

    nuevos = ["clas_tipo", "clas_vertical", "clas_estado_real"]
    n = con_clas = 0
    with open(src, encoding="utf-8-sig", newline="") as fi, \
            open(dst, "w", encoding="utf-8-sig", newline="") as fo:
        rd = csv.DictReader(fi)
        wr = csv.DictWriter(fo, fieldnames=list(rd.fieldnames) + nuevos)
        wr.writeheader()
        for row in rd:
            n += 1
            c = cache.get((row.get("Numero") or "").strip())
            if c:
                con_clas += 1
                row["clas_tipo"] = c.get("tipo")
                row["clas_vertical"] = "si" if c.get("vertical") else "no"
                row["clas_estado_real"] = ce._canon_estado(c.get("estado_real")) or ""
            else:
                row["clas_tipo"] = row["clas_vertical"] = row["clas_estado_real"] = ""
            wr.writerow(row)

    print(f"✅ Exportado: {dst}")
    print(f"   {n} reportes ({con_clas} con clasificación).")
    print("   ⚠️ Contiene PII (cédula/teléfono/email). NO versionar ni compartir externamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

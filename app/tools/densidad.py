"""Densidad poblacional por localidad (hab/km²).

Cruza la intensidad sísmica/población (`data_seed/intensidad_mmi_24j.csv`) con el
área municipal (`data_seed/areas_municipios.csv`) para expresar exposición como
**densidad** en vez de población absoluta. Donde no hay área disponible, marca N/D.
"""
from __future__ import annotations
import csv
import os
import unicodedata

_BASE = os.path.join(os.path.dirname(__file__), "..", "..", "data_seed")
_MMI = os.path.join(_BASE, "intensidad_mmi_24j.csv")
_AREAS = os.path.join(_BASE, "areas_municipios.csv")


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def _areas() -> dict:
    out = {}
    if not os.path.exists(_AREAS):
        return out
    with open(_AREAS, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                out[_norm(r["localidad"])] = {
                    "municipio": r.get("municipio", ""),
                    "area_km2": float(r["area_km2"]),
                    "tipo": r.get("tipo", ""),
                }
            except (ValueError, KeyError):
                continue
    return out


def densidades() -> list[dict]:
    """Lista [{localidad, mmi, habitantes, area_km2, densidad, aprox, ...}]."""
    areas = _areas()
    filas = []
    if not os.path.exists(_MMI):
        return filas
    with open(_MMI, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                hab = int(float(r["habitantes"]))
                mmi = float(r["mmi"])
            except (ValueError, KeyError):
                continue
            a = areas.get(_norm(r["localidad"]))
            dens = round(hab / a["area_km2"]) if a else None
            filas.append({
                "localidad": r["localidad"],
                "mmi": mmi,
                "habitantes": hab,
                "area_km2": a["area_km2"] if a else None,
                "densidad": dens,
                "municipio": a["municipio"] if a else None,
                # cota inferior si el area es municipal/estadal y la localidad es parroquia
                "aprox": bool(a and "area municipal" in (a.get("tipo") or "")),
            })
    return filas


def densidad_de(localidad: str) -> dict | None:
    n = _norm(localidad)
    for d in densidades():
        if _norm(d["localidad"]) == n:
            return d
    return None


def tabla_densidad_md(top: int = 12, solo_con_area: bool = True) -> str:
    """Tabla markdown de densidad por localidad (orden desc por densidad)."""
    filas = [d for d in densidades() if (d["densidad"] is not None or not solo_con_area)]
    filas.sort(key=lambda d: (d["densidad"] or -1), reverse=True)
    out = ["| Localidad | MMI | Densidad (hab/km²) | Área km² |", "|---|---|---|---|"]
    for d in filas[:top]:
        dens = f"{d['densidad']:,}".replace(",", ".") + (" *" if d["aprox"] else "") if d["densidad"] else "N/D"
        out.append(f"| {d['localidad']} | {d['mmi']:.1f} | {dens} | {d['area_km2'] or 'N/D'} |")
    out.append("")
    out.append("\\* densidad calculada con área municipal completa (cota inferior).")
    return "\n".join(out)

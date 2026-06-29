"""Dataset de referencia de intensidad sísmica MMI por localidad (Terremoto 24J).

Fuente: tabla de El País / ShakeMap-USGS del 24J. Carga y normaliza el CSV
`data_seed/intensidad_mmi_24j.csv` (sin PII ni secretos; se versiona).

IMPORTANTE: `peso_mmi` es un proxy heurístico de fracción de daño potencial,
NO una estimación de víctimas. El `indice_exposicion` aproxima "personas
potencialmente expuestas a daño relevante", no un conteo real de afectados.
"""
from __future__ import annotations

import csv
import os
import re
import unicodedata
from functools import lru_cache

from pydantic import BaseModel

# Ruta al CSV versionado (raíz del repo / data_seed).
_CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data_seed", "intensidad_mmi_24j.csv",
)

# Epicentros aproximados (Yaracuy / eje costa central) para realce por cercanía.
EPICENTROS = [("San Felipe", 10.34, -68.74), ("Yumare", 10.61, -68.70)]


def normalizar_nombre(nombre: str) -> str:
    """minúsculas, sin acentos, sin sufijos '(1)/(2)', espacios colapsados."""
    s = (nombre or "").strip().lower()
    s = re.sub(r"\(\s*\d+\s*\)", "", s)  # sufijos (1), (2)
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = re.sub(r"\s+", " ", s).strip()
    return s


def peso_mmi(mmi: float) -> float:
    """Proxy heurístico de fracción de daño potencial (NO estimación de víctimas)."""
    if mmi < 4.5:
        return 0.05
    if mmi < 5.5:
        return 0.15
    if mmi < 6.0:
        return 0.35
    if mmi < 6.5:
        return 0.60
    if mmi < 7.0:
        return 0.80
    if mmi < 8.0:
        return 1.00
    return 1.20


class LocalidadMMI(BaseModel):
    localidad: str
    mmi: float
    habitantes: int
    pais: str
    fuente: str
    # Derivados.
    localidad_norm: str = ""
    peso_mmi: float = 0.0
    indice_exposicion: float = 0.0


def _parse_row(row: dict) -> LocalidadMMI | None:
    try:
        mmi = float(str(row.get("mmi", "")).replace(",", "."))
        hab = int(float(str(row.get("habitantes", "0")).replace(".", "").replace(",", "") or 0))
    except (TypeError, ValueError):
        return None
    nombre = (row.get("localidad") or "").strip()
    if not nombre:
        return None
    w = peso_mmi(mmi)
    return LocalidadMMI(
        localidad=nombre,
        mmi=mmi,
        habitantes=hab,
        pais=(row.get("pais") or "").strip() or "VE",
        fuente=(row.get("fuente") or "").strip(),
        localidad_norm=normalizar_nombre(nombre),
        peso_mmi=w,
        indice_exposicion=round(hab * w, 1),
    )


@lru_cache(maxsize=4)
def _cargar_raw(path: str) -> tuple[LocalidadMMI, ...]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"No se encontró el dataset MMI: {path}")
    out: list[LocalidadMMI] = []
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            loc = _parse_row(row)
            if loc:
                out.append(loc)
    return tuple(out)


def cargar_mmi(solo_venezuela: bool = True, path: str | None = None) -> list[LocalidadMMI]:
    """Carga el CSV de intensidad MMI (cacheado). Por defecto solo Venezuela."""
    datos = _cargar_raw(path or _CSV_PATH)
    if solo_venezuela:
        datos = tuple(d for d in datos if d.pais.upper() == "VE")
    # Orden por intensidad y exposición (las más críticas primero).
    return sorted(datos, key=lambda d: (d.mmi, d.indice_exposicion), reverse=True)

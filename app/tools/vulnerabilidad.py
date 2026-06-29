"""Vulnerabilidad per cápita — Terremoto 24J (dataset curado en Markdown).

Lee `vulnerabilidad_estado_municipio_parroquia.md` (entregado por la Sala
Situacional VenApp) y expone el ranking de **afectación per cápita** (índice
0–100 %) por estado / municipio / parroquia, ponderando severidad
(desaparecidos ×4, viviendas colapsadas ×2, casos críticos) sobre la población.

Sirve para responder "¿qué entidades están más afectadas EN FUNCIÓN DE LA
CANTIDAD DE PERSONAS?", que en absolutos quedaría sesgado hacia las zonas más
pobladas (Caracas). Solo lectura; el .md no contiene PII.
"""
from __future__ import annotations

import os
import re
from functools import lru_cache

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mapea encabezados del .md -> claves de salida (normalizadas).
_KEYMAP = {
    "estado": "estado",
    "municipio": "municipio",
    "parroquia": "parroquia",
    "población": "poblacion",
    "poblacion": "poblacion",
    "mmi": "mmi",
    "reportes": "reportes",
    "desap.": "desaparecidos",
    "colaps.": "colapsadas",
    "críticos": "criticos",
    "criticos": "criticos",
    "rep/10k": "rep_10k",
    "vulnerab.": "vulnerabilidad_pct",
}
_NUM_KEYS = {"poblacion", "reportes", "desaparecidos", "colapsadas", "criticos",
             "rep_10k", "vulnerabilidad_pct"}


def vulnerabilidad_path() -> str | None:
    env = os.environ.get("VENAPP_VULN_PATH")
    if env and os.path.exists(env):
        return env
    p = os.path.join(_ROOT, "vulnerabilidad_estado_municipio_parroquia.md")
    return p if os.path.exists(p) else None


def vulnerabilidad_disponible() -> bool:
    return vulnerabilidad_path() is not None


def _num(s: str):
    s = s.replace("*", "").replace("%", "").replace(",", "").strip()
    if s in ("", "—", "-"):
        return None
    try:
        return int(s) if re.fullmatch(r"-?\d+", s) else float(s)
    except ValueError:
        return s


def _parse_tabla(lineas: list[str]) -> list[dict]:
    """Parsea un bloque de tabla Markdown (lista de líneas que empiezan con '|')."""
    filas_md = [ln for ln in lineas if ln.strip().startswith("|")]
    if len(filas_md) < 2:
        return []

    def celdas(ln: str) -> list[str]:
        return [c.strip() for c in ln.strip().strip("|").split("|")]

    encabezados = [h.lower().replace("*", "").strip() for h in celdas(filas_md[0])]
    out: list[dict] = []
    for ln in filas_md[1:]:
        if set(ln.replace("|", "").strip()) <= set(":- "):  # línea separadora
            continue
        vals = celdas(ln)
        fila: dict = {}
        for h, v in zip(encabezados, vals):
            clave = _KEYMAP.get(h)
            if not clave or clave == "#" or h == "#":
                continue
            fila[clave] = _num(v) if clave in _NUM_KEYS else (v.replace("*", "").strip() or None)
        if fila.get("estado") or fila.get("municipio") or fila.get("parroquia"):
            out.append(fila)
    return out


@lru_cache(maxsize=1)
def _cargar() -> dict:
    path = vulnerabilidad_path()
    if not path:
        raise RuntimeError("No se encontró vulnerabilidad_estado_municipio_parroquia.md")
    with open(path, encoding="utf-8") as fh:
        texto = fh.read()

    corte = ""
    m = re.search(r"Corte de datos:\s*\*\*([^*]+)\*\*", texto)
    if m:
        corte = m.group(1).strip()

    # Trocea por secciones de nivel (## 1) Estados / ## 2) Municipios / ## 3) Parroquias).
    secciones = re.split(r"\n##\s+", texto)
    niveles: dict[str, list[dict]] = {"estado": [], "municipio": [], "parroquia": []}
    for sec in secciones:
        head = sec.splitlines()[0].lower() if sec.strip() else ""
        if "estado" in head and "municipio" not in head:
            niveles["estado"] = _parse_tabla(sec.splitlines())
        elif "municipio" in head:
            niveles["municipio"] = _parse_tabla(sec.splitlines())
        elif "parroquia" in head:
            niveles["parroquia"] = _parse_tabla(sec.splitlines())
    return {"corte": corte, "niveles": niveles}


def consultar_vulnerabilidad(nivel: str = "estado", estado: str | None = None,
                             top: int = 15) -> dict:
    """Ranking de afectación per cápita.

    nivel: 'estado' | 'municipio' | 'parroquia'.
    estado: filtra a una entidad (para 'municipio'/'parroquia').
    top: máximo de filas (ya vienen ordenadas por vulnerabilidad desc en el .md).
    """
    data = _cargar()
    nivel = (nivel or "estado").lower()
    if nivel not in data["niveles"]:
        nivel = "estado"
    filas = data["niveles"][nivel]
    if estado:
        obj = estado.strip().lower()
        filas = [f for f in filas if (f.get("estado") or "").strip().lower() == obj]
    filas = sorted(filas, key=lambda f: f.get("vulnerabilidad_pct") or 0, reverse=True)
    return {
        "nivel": nivel,
        "corte_datos": data["corte"],
        "estado_filtro": estado,
        "metodologia": ("Índice de afectación per cápita 0–100% (100=máx del nivel); "
                        "pondera desaparecidos×4, viviendas colapsadas×2 y casos críticos, "
                        "sobre (población+20.000). Reencuadra la afectación POR HABITANTE."),
        "ranking": filas[: top or len(filas)],
    }

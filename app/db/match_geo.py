"""Emparejamiento de localidades MMI (El País) ↔ geografía VenApp.

Estrategia de mayor a menor confianza:
  1. Mapa manual curado (MAPA_LOCALIDAD_VENAPP) para las localidades de alta
     intensidad (las que más importan). Confianza ALTA.
  2. Match difuso (rapidfuzz) contra los catálogos reales de VenApp:
     parroquia.name → municipality.name → province.name. Confianza media/baja.
  3. Sin match → granularidad="sin_match" (se reporta aparte).

Diseñado para ser AUDITABLE: cada match expone confianza y granularidad.
Solo lectura sobre VenApp (los catálogos salen de `distinct` con filtro de evento).
"""
from __future__ import annotations

from functools import lru_cache

from app.db.intensidad_mmi import normalizar_nombre

try:  # rapidfuzz es opcional: sin él, solo funciona el mapa curado.
    from rapidfuzz import fuzz, process  # type: ignore
    _HAS_RAPIDFUZZ = True
except Exception:  # noqa: BLE001
    _HAS_RAPIDFUZZ = False

UMBRAL_FUZZY = 88  # score mínimo (0-100) para aceptar un match difuso.

# --------------------------------------------------------------------------- #
# Mapa manual curado — cubre todas las MMI ≥ 6,0 (alta intensidad).
# Cada entrada: localidad_norm -> (estado, municipio|None, parroquia|None)
# --------------------------------------------------------------------------- #
MAPA_LOCALIDAD_VENAPP: dict[str, tuple[str, str | None, str | None]] = {
    # La Guaira (antes Vargas) — eje costa central.
    "maiquetia": ("La Guaira", "Vargas", "Maiquetía"),
    "catia la mar": ("La Guaira", "Vargas", "Catia La Mar"),
    "caraballeda": ("La Guaira", "Vargas", "Caraballeda"),
    "la guaira": ("La Guaira", "Vargas", "La Guaira"),
    "ocumare de la costa": ("Aragua", "Ocumare de la Costa de Oro", "Ocumare de la Costa"),
    # Caracas / Miranda. (En los datos VenApp la provincia es 'Caracas'.)
    "caracas": ("Caracas", None, None),
    "petare": ("Miranda", "Sucre", "Petare"),
    "baruta": ("Miranda", "Baruta", "Baruta"),
    "los teques": ("Miranda", "Guaicaipuro", "Los Teques"),
    # Carabobo / Falcón — eje costero norte.
    "puerto cabello": ("Carabobo", "Puerto Cabello", None),
    "tucacas": ("Falcón", "José Laurencio Silva", "Tucacas"),
    "chichiriviche": ("Falcón", "Monseñor Iturriza", "Chichiriviche"),
    "valencia": ("Carabobo", "Valencia", None),
    "guacara": ("Carabobo", "Guacara", None),
    "los guayos": ("Carabobo", "Los Guayos", None),
    "san diego": ("Carabobo", "San Diego", None),
    "tocuyito": ("Carabobo", "Libertador", "Tocuyito"),
    "santa rita": ("Aragua", "Francisco Linares Alcántara", "Santa Rita"),
    # Aragua.
    "maracay": ("Aragua", "Girardot", None),
    "cagua": ("Aragua", "Sucre", "Cagua"),
    "palo negro": ("Aragua", "Libertador", "Palo Negro"),
    "turmero": ("Aragua", "Santiago Mariño", "Turmero"),
    "el limon": ("Aragua", "Mario Briceño Iragorry", "El Limón"),
    "la victoria": ("Aragua", "José Félix Ribas", "La Victoria"),
    "santa cruz": ("Aragua", "José Ángel Lamas", "Santa Cruz"),
    "la colonia tovar": ("Aragua", "Tovar", "La Colonia Tovar"),
    # Yaracuy — eje epicentral.
    "san felipe": ("Yaracuy", "San Felipe", None),
    "yaritagua": ("Yaracuy", "Peña", "Yaritagua"),
    "yumare": ("Yaracuy", "Manuel Monge", "Yumare"),
}


class MatchGeo:
    """Resultado de emparejamiento (auditable)."""

    def __init__(self, estado=None, municipio=None, parroquia=None,
                 granularidad="sin_match", confianza="baja", score=0.0):
        self.estado = estado
        self.municipio = municipio
        self.parroquia = parroquia
        self.granularidad = granularidad  # parroquia | municipio | estado | sin_match
        self.confianza = confianza        # alta | media | baja
        self.score = score

    def as_dict(self) -> dict:
        return {
            "estado": self.estado, "municipio": self.municipio, "parroquia": self.parroquia,
            "granularidad": self.granularidad, "confianza": self.confianza,
            "score": round(self.score, 1),
        }


@lru_cache(maxsize=1)
def _catalogos_venapp() -> dict:
    """Catálogos reales de VenApp (distinct con filtro de evento). Degrada a {}
    si la BD no está accesible (entorno sin red interna)."""
    try:
        from app.db.data_service import _col
        from app.db.mongo import build_event_query, reports_source_available
        if not reports_source_available():
            return {"parroquia": [], "municipio": [], "estado": []}
        q = build_event_query()
        col = _col()
        return {
            "parroquia": [v for v in col.distinct("parroquia.name", q) if v],
            "municipio": [v for v in col.distinct("municipality.name", q) if v],
            "estado": [v for v in col.distinct("province.name", q) if v],
        }
    except Exception:  # noqa: BLE001 — sin BD, el mapa curado sigue funcionando
        return {"parroquia": [], "municipio": [], "estado": []}


@lru_cache(maxsize=64)
def _nombres_nivel(estado: str | None, campo: str) -> frozenset:
    """Conjunto NORMALIZADO de nombres de `campo` ('parroquia.name' o
    'municipality.name') que existen DENTRO de `estado`. Evita falsos positivos
    cuando un nombre de parroquia existe en otra provincia (p. ej. 'Santa Cruz')."""
    if not estado:
        return frozenset()
    try:
        from app.db.data_service import _col
        from app.db.mongo import build_event_query, reports_source_available
        if not reports_source_available():
            return frozenset()
        q = build_event_query(province=estado)
        return frozenset(normalizar_nombre(v) for v in _col().distinct(campo, q) if v)
    except Exception:  # noqa: BLE001
        return frozenset()


def _resolver_catalogo(nombre: str | None, candidatos: list[str]) -> str | None:
    """Devuelve el valor REAL del catálogo (tal como está almacenado) cuyo nombre
    normalizado coincide con `nombre`. Corrige diferencias de acentos/mayúsculas
    (p. ej. mapa 'Maiquetía' → dato 'Maiquetia'). Si no hay match, deja el original."""
    if not nombre or not candidatos:
        return nombre
    objetivo = normalizar_nombre(nombre)
    for c in candidatos:
        if normalizar_nombre(c) == objetivo:
            return c
    return nombre


def _fuzzy_best(nombre_norm: str, candidatos: list[str]) -> tuple[str | None, float]:
    if not (_HAS_RAPIDFUZZ and candidatos):
        return None, 0.0
    norm_map = {normalizar_nombre(c): c for c in candidatos}
    res = process.extractOne(nombre_norm, list(norm_map.keys()), scorer=fuzz.WRatio)
    if not res:
        return None, 0.0
    match_norm, score, _ = res
    return norm_map[match_norm], float(score)


def emparejar_localidad(localidad: str) -> MatchGeo:
    """Empareja una localidad MMI con la geografía de VenApp (auditable)."""
    norm = normalizar_nombre(localidad)

    # 1) Mapa curado (confianza alta). Resolvemos cada nivel al valor REAL del
    #    catálogo VenApp (corrige acentos/mayúsculas: 'Maiquetía'→'Maiquetia') y
    #    elegimos la granularidad MÁS FINA QUE EXISTA en los datos: muchas
    #    localidades se almacenan a nivel municipio, no parroquia, y consultarlas
    #    como parroquia daría 0 reportes falso (zona "silenciosa" inexistente).
    if norm in MAPA_LOCALIDAD_VENAPP:
        estado_c, muni_c, parr_c = MAPA_LOCALIDAD_VENAPP[norm]
        cat = _catalogos_venapp()
        estado = _resolver_catalogo(estado_c, cat.get("estado", []))
        muni = _resolver_catalogo(muni_c, cat.get("municipio", []))
        parr = _resolver_catalogo(parr_c, cat.get("parroquia", []))
        # Existencia comprobada DENTRO de la provincia resuelta.
        parr_estado = _nombres_nivel(estado, "parroquia.name")
        muni_estado = _nombres_nivel(estado, "municipality.name")
        if parr_c and normalizar_nombre(parr_c) in parr_estado:
            gran = "parroquia"
        elif muni_c and normalizar_nombre(muni_c) in muni_estado:
            gran, parr = "municipio", None
        elif (parr_estado or muni_estado) and estado:
            # Ni la parroquia ni el municipio existen en esa provincia: cae a estado.
            gran, muni, parr = "estado", None, None
        else:
            # Sin catálogo (BD y Excel ausentes): comportamiento original.
            gran = "parroquia" if parr else ("municipio" if muni else "estado")
        return MatchGeo(estado, muni, parr, granularidad=gran, confianza="alta", score=100.0)

    # 2) Match difuso contra catálogos reales (parroquia → municipio → estado).
    cat = _catalogos_venapp()
    for nivel, gran, conf in (("parroquia", "parroquia", "media"),
                              ("municipio", "municipio", "media"),
                              ("estado", "estado", "baja")):
        match, score = _fuzzy_best(norm, cat.get(nivel, []))
        if match and score >= UMBRAL_FUZZY:
            kw = {gran: match}
            return MatchGeo(
                estado=kw.get("estado"), municipio=kw.get("municipio"),
                parroquia=kw.get("parroquia"), granularidad=gran,
                confianza=conf, score=score,
            )

    # 3) Sin match.
    return MatchGeo(granularidad="sin_match", confianza="baja", score=0.0)

"""Motor de cruce intensidad MMI × población × reportes recibidos → puntos ciegos.

Detecta **zonas silenciosas / puntos ciegos**: localidades de alta intensidad y
mucha población con pocos o cero reportes en VenApp. Regla rectora obligatoria:
**baja/nula recepción de reportes NO significa ausencia de daño** — es una *zona
de atención* (probable caída de conectividad/energía, daño a infraestructura,
cercanía al epicentro) y debe priorizarse para verificación en terreno.

Solo lectura sobre VenApp; el cruce nunca escribe en producción. El análisis es
agregado por localidad (sin PII). `peso_mmi`/umbrales son heurísticas
configurables, no estimaciones de víctimas.
"""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field

from app.db.intensidad_mmi import EPICENTROS, cargar_mmi
from app.db.match_geo import emparejar_localidad

_ADVERTENCIA = (
    "Baja o nula recepción de reportes NO implica ausencia de daño: se trata como "
    "ZONA DE ATENCIÓN, no como zona sin problema. Causas probables: caída de "
    "conectividad/energía, daño a infraestructura o cercanía al epicentro."
)


class ZonaCiega(BaseModel):
    localidad: str
    estado: str | None = None
    municipio: str | None = None
    parroquia: str | None = None
    mmi: float
    habitantes: int
    indice_exposicion: float
    reportes_observados: int
    reportes_esperados: float
    cobertura: float
    indice_punto_ciego: float
    critica: bool
    confianza_match: str
    granularidad: str
    interpretacion: str


class AnalisisPuntosCiegos(BaseModel):
    generado_en: dt.datetime = Field(default_factory=dt.datetime.now)
    parametros: dict = Field(default_factory=dict)
    datos_reportes_disponibles: bool = True
    zonas_criticas: list[ZonaCiega] = Field(default_factory=list)
    zonas_silenciosas: list[ZonaCiega] = Field(default_factory=list)
    zonas_visibles: list[ZonaCiega] = Field(default_factory=list)
    sin_match: list[str] = Field(default_factory=list)
    resumen: str = ""


# --------------------------------------------------------------------------- #
# Conteo de reportes observados por zona (solo lectura, con filtro de evento)
# --------------------------------------------------------------------------- #
def _contar_reportes(match) -> int | None:
    """Cuenta reportes de VenApp en la zona del match. Devuelve None si la BD no
    está accesible (entorno sin red interna / VPN apagada)."""
    try:
        from app.db.data_service import _col
        from app.db.mongo import build_event_query, reports_source_available
        if not reports_source_available():
            return None
        q = build_event_query(province=match.estado) if match.estado else build_event_query()
        if match.granularidad == "parroquia" and match.parroquia:
            q["parroquia.name"] = match.parroquia
        elif match.granularidad == "municipio" and match.municipio:
            q["municipality.name"] = match.municipio
        return _col().count_documents(q)
    except Exception:  # noqa: BLE001
        return None


def _cerca_epicentro(estado: str | None) -> bool:
    if not estado:
        return False
    est = estado.lower()
    return est in {"yaracuy", "la guaira", "aragua", "carabobo", "falcon", "falcón"}


def _interpretar(z: dict, critica: bool) -> str:
    base = (
        f"{z['localidad']} registró intensidad MMI {z['mmi']} con ~{z['habitantes']:,} "
        f"habitantes; reportes recibidos: {z['obs']} frente a "
        f"{round(z['esperados'])} esperados (cobertura {z['cobertura']:.0%}). "
    ).replace(",", ".")
    if critica:
        return base + "CRÍTICA: alta exposición y casi sin reportes → " + _ADVERTENCIA
    if z["cobertura"] < 0.6:
        return base + "Recepción baja → vigilar como zona de atención. " + _ADVERTENCIA
    return base + "Cobertura de reportes adecuada (zona visible / control)."


def analizar_puntos_ciegos(umbral_mmi: float = 6.0,
                           umbral_habitantes: int = 20000,
                           umbral_cobertura: float = 0.25,
                           top: int | None = None) -> AnalisisPuntosCiegos:
    localidades = cargar_mmi(solo_venezuela=True)

    # 1-2) Emparejar y contar reportes observados.
    filas: list[dict] = []
    sin_match: list[str] = []
    datos_disponibles = False
    for loc in localidades:
        m = emparejar_localidad(loc.localidad)
        if m.granularidad == "sin_match":
            sin_match.append(loc.localidad)
            continue
        obs = _contar_reportes(m)
        if obs is not None:
            datos_disponibles = True
        filas.append({
            "localidad": loc.localidad, "mmi": loc.mmi, "habitantes": loc.habitantes,
            "indice_exposicion": loc.indice_exposicion, "peso_mmi": loc.peso_mmi,
            "match": m, "obs": obs or 0,
        })

    # 3) Tasa global entre localidades que SÍ reportan.
    reportan = [f for f in filas if f["obs"] > 0]
    suma_obs = sum(f["obs"] for f in reportan)
    suma_exp = sum(f["indice_exposicion"] for f in reportan) or 1.0
    tasa_global = (suma_obs / suma_exp) if suma_obs > 0 else None

    # 4) Métricas por localidad.
    for f in filas:
        if tasa_global is not None:
            f["esperados"] = f["indice_exposicion"] * tasa_global
            f["deficit"] = max(0.0, f["esperados"] - f["obs"])
            f["cobertura"] = f["obs"] / max(f["esperados"], 1.0)
        else:
            # Sin datos de reportes: proxy por exposición (todo "no observado").
            f["esperados"] = 0.0
            f["deficit"] = f["indice_exposicion"]
            f["cobertura"] = 0.0

    max_def = max((f["deficit"] for f in filas), default=0.0) or 1.0
    for f in filas:
        deficit_norm = 100.0 * f["deficit"] / max_def
        realce = 1.1 if _cerca_epicentro(f["match"].estado) else 1.0
        f["indice_punto_ciego"] = round(min(120.0, deficit_norm * f["peso_mmi"] * realce), 1)

    # 5) Clasificación.
    criticas: list[ZonaCiega] = []
    silenciosas: list[ZonaCiega] = []
    visibles: list[ZonaCiega] = []
    for f in filas:
        critica = (f["mmi"] >= umbral_mmi and f["habitantes"] >= umbral_habitantes
                   and f["cobertura"] < umbral_cobertura)
        m = f["match"]
        z = ZonaCiega(
            localidad=f["localidad"], estado=m.estado, municipio=m.municipio,
            parroquia=m.parroquia, mmi=f["mmi"], habitantes=f["habitantes"],
            indice_exposicion=f["indice_exposicion"], reportes_observados=f["obs"],
            reportes_esperados=round(f["esperados"], 1), cobertura=round(f["cobertura"], 3),
            indice_punto_ciego=f["indice_punto_ciego"], critica=critica,
            confianza_match=m.confianza, granularidad=m.granularidad,
            interpretacion=_interpretar(f, critica),
        )
        if critica:
            criticas.append(z)
        elif f["cobertura"] < 0.6:
            silenciosas.append(z)
        else:
            visibles.append(z)

    criticas.sort(key=lambda z: z.indice_punto_ciego, reverse=True)
    silenciosas.sort(key=lambda z: z.indice_punto_ciego, reverse=True)
    visibles.sort(key=lambda z: z.indice_punto_ciego, reverse=True)
    if top:
        criticas = criticas[:top]
        silenciosas = silenciosas[:top]

    nombres_top = ", ".join(z.localidad for z in criticas[:5]) or "ninguna"
    nota_datos = "" if datos_disponibles else (
        " [AVISO: no se pudo leer la BD de VenApp; el ranking usa exposición "
        "(MMI×población) como proxy hasta tener conteos reales de reportes.]"
    )
    resumen = (
        f"{len(criticas)} zonas CRÍTICAS y {len(silenciosas)} silenciosas detectadas por el "
        f"cruce intensidad×población×reportes. Prioridad de verificación en terreno: {nombres_top}. "
        f"{_ADVERTENCIA}{nota_datos}"
    )

    return AnalisisPuntosCiegos(
        parametros={"umbral_mmi": umbral_mmi, "umbral_habitantes": umbral_habitantes,
                    "umbral_cobertura": umbral_cobertura, "top": top,
                    "epicentros": EPICENTROS},
        datos_reportes_disponibles=datos_disponibles,
        zonas_criticas=criticas, zonas_silenciosas=silenciosas,
        zonas_visibles=visibles, sin_match=sin_match, resumen=resumen,
    )

"""IPCT — Índice de Prioridad Crítica Territorial (Terremoto 24J).

Prioriza PARROQUIAS (unidad: parroquia; cuadrante donde exista — aún no hay capa
de cuadrantes, así que se trabaja por parroquia) según la convergencia de cinco
factores, normalizados 0–5 (5 = máxima prioridad):

  F1 Intensidad sísmica          (MMI por parroquia)
  F2 Densidad poblacional         (población expuesta — pend. km² para densidad real)
  F3 Construcción vertical        (PROXY: reportes de 'Edificio con riesgo de colapso';
                                   pend. capa GIS de edificación vertical de Chumaceiro)
  F4 Densidad de reportes         (reportes por 10.000 hab)
  F5 Daño estructural reportado   (viviendas colapsadas + daño estructural grave)

IPCT = 0,20·F1 + 0,20·F2 + 0,20·F3 + 0,15·F4 + 0,25·F5   (ponderación André).

Cálculo DETERMINISTA en código (no lo estima el modelo) para que sea exacto y
auditable. Cada factor se normaliza por min-max entre las parroquias analizadas:
5 = la más alta del conjunto. Solo lectura; sin PII (agregados por parroquia).
"""
from __future__ import annotations

import datetime as dt
import math
from functools import lru_cache

from app.db.intensidad_mmi import normalizar_nombre
from app.db.mongo import build_event_query, get_reports_collection
from app.tools.vulnerabilidad import consultar_vulnerabilidad

# Romano MMI -> entero.
_MMI = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8,
        "IX": 9, "X": 10, "XI": 11, "XII": 12}

# Extracategorías que indican POSIBLES SOBREVIVIENTES / vidas en juego.
_CAT_SOBREVIVIENTES = (
    "persona atrapada bajo escombros",
    "persona que requiere rescate",
    "persona desaparecida",
    "persona herida",
)
# Subconjunto más urgente (vida bajo escombros) para el filtro de las 72 h.
_CAT_RESCATE_URGENTE = (
    "persona atrapada bajo escombros",
    "persona que requiere rescate",
)
_CAT_VERTICAL = ("edificio con riesgo de colapso",)
_STATUS_ATENDIDO = {"atendido"}

# Fallback por palabras clave (título/descripción) cuando el export NO trae la
# taxonomía fina de `extracategory` (export nuevo `terremoto*.csv`, que solo tiene
# 'Subcategoria' gruesa). Así no se reportan 0 sobrevivientes cuando sí los hay.
import re as _re  # noqa: E402
_RX_SOBREVIVIENTE = _re.compile(
    r"atrapad|bajo (los )?escombros|sepultad|soterrad|desaparec|no aparece|"
    r"paradero|herid|rescat", _re.IGNORECASE)
_RX_RESCATE_URGENTE = _re.compile(
    r"atrapad|bajo (los )?escombros|sepultad|soterrad|rescat", _re.IGNORECASE)

# Ponderaciones del IPCT v1 (suman 1.0). 'construccion_vertical' NO entra en el
# cálculo v1 (no hay capa GIS real; el proxy de reportes de edificio sesga hacia
# las zonas que más reportan). Se muestra aparte como informativo/pendiente y su
# 20% original se redistribuye hacia gravedad e intensidad.
_PESOS = {"dano": 0.35, "reportes": 0.20, "intensidad": 0.25, "densidad_pob": 0.20}
_FACTORES_IPCT = ("intensidad", "densidad_pob", "reportes", "dano")


def _norm(nombre: str | None) -> str:
    return normalizar_nombre(nombre or "")


def _mmi_num(roman: str | None):
    if not roman:
        return None
    return _MMI.get(str(roman).strip().upper())


def _minmax_0_5(valores: dict[str, float]) -> dict[str, float]:
    """Normaliza un dict {clave: valor} a 0–5 por min-max (5 = máximo del conjunto)."""
    nums = [v for v in valores.values() if v is not None]
    if not nums:
        return {k: 0.0 for k in valores}
    lo, hi = min(nums), max(nums)
    rng = (hi - lo) or 1.0
    return {k: (0.0 if v is None else round(5.0 * (v - lo) / rng, 2)) for k, v in valores.items()}


def _nivel(ipct: float) -> str:
    if ipct >= 4.0:
        return "Crítica"
    if ipct >= 3.0:
        return "Alta"
    if ipct >= 2.0:
        return "Media"
    return "Baja"


# --------------------------------------------------------------------------- #
# Agregados por parroquia desde el Excel/BD (sobrevivientes, vertical, recencia)
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def _agregados_parroquia() -> dict:
    """Por (estado_norm, parroquia_norm): conteos de sobrevivientes/rescate/
    vertical/no-atendidos y el último reporte de sobreviviente (fecha)."""
    col = get_reports_collection()
    docs = list(col.find(build_event_query()))
    # ¿El export trae la taxonomía fina de extracategory? Si NO (export nuevo),
    # detectamos sobrevivientes/rescate por palabras clave en título/descripción.
    usa_taxonomia_fina = any(
        _norm((d.get("extracategory") or {}).get("name")) in _CAT_SOBREVIVIENTES
        for d in docs
    )
    agg: dict[tuple, dict] = {}
    ref_now = None
    for d in docs:
        ts = d.get("createdAt")
        if isinstance(ts, dt.datetime):
            ref_now = ts if ref_now is None or ts > ref_now else ref_now
        prov = _norm((d.get("province") or {}).get("name"))
        parr = _norm((d.get("parroquia") or {}).get("name"))
        if not parr:
            continue
        key = (prov, parr)
        a = agg.setdefault(key, {
            "sobrevivientes": 0, "rescate_urgente": 0, "vertical": 0,
            "sobrev_no_atendidos": 0, "ultimo_sobreviviente": None,
        })
        ext = _norm((d.get("extracategory") or {}).get("name"))
        status = _norm(d.get("status"))
        if usa_taxonomia_fina:
            es_sobreviviente = ext in _CAT_SOBREVIVIENTES
            es_rescate_urgente = ext in _CAT_RESCATE_URGENTE
            if ext in _CAT_VERTICAL:
                a["vertical"] += 1
        else:
            txt = f"{d.get('title') or ''} {d.get('description') or ''}"
            es_sobreviviente = bool(_RX_SOBREVIVIENTE.search(txt))
            es_rescate_urgente = bool(_RX_RESCATE_URGENTE.search(txt))
        if es_sobreviviente:
            a["sobrevivientes"] += 1
            if status not in _STATUS_ATENDIDO:
                a["sobrev_no_atendidos"] += 1
            if isinstance(ts, dt.datetime):
                if a["ultimo_sobreviviente"] is None or ts > a["ultimo_sobreviviente"]:
                    a["ultimo_sobreviviente"] = ts
        if es_rescate_urgente and status not in _STATUS_ATENDIDO:
            a["rescate_urgente"] += 1
    return {"por_parroquia": agg, "ref_now": ref_now or dt.datetime(2026, 6, 26, 12, 44)}


# --------------------------------------------------------------------------- #
# Hito 1 — IPCT por parroquia
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def _calcular() -> list[dict]:
    base = consultar_vulnerabilidad("parroquia", top=200)["ranking"]
    agg = _agregados_parroquia()["por_parroquia"]

    # Valores crudos por parroquia para cada factor.
    crudos: dict[str, dict] = {}
    meta: dict[str, dict] = {}
    for r in base:
        estado = r.get("estado"); muni = r.get("municipio"); parr = r.get("parroquia")
        if not parr:
            continue
        clave = f"{_norm(estado)}|{_norm(parr)}"
        a = agg.get((_norm(estado), _norm(parr)), {})
        pob = r.get("poblacion") or 0
        rep = r.get("reportes") or 0
        colaps = r.get("colapsadas") or 0
        desap = r.get("desaparecidos") or 0
        criticos = r.get("criticos") or 0
        vertical = a.get("vertical", 0)
        # Factores de VOLUMEN se miden PER CÁPITA (por 10.000 hab) con suavizado
        # +20.000 (como el índice de vulnerabilidad): así prioriza por gravedad
        # relativa a la población, no por tamaño absoluto de la zona.
        pob_s = pob + 20000
        # F5 = daño estructural y AFECTACIÓN GRAVE: pondera colapsos×2, desaparecidos×4
        # y casos críticos (vidas), per cápita. Captura la severidad humana real.
        gravedad = (2 * colaps + 4 * desap + criticos) / pob_s * 10000
        # Raíz cuadrada en los factores per cápita: estabiliza la asimetría (una
        # parroquia extrema no aplasta la escala) y reparte mejor el 0–5.
        crudos[clave] = {
            "intensidad": _mmi_num(r.get("mmi")) or 0,           # absoluto (MMI)
            "densidad_pob": math.sqrt(pob),                      # exposición (sublineal)
            "vertical": math.sqrt(vertical / pob_s * 10000),     # per cápita
            "reportes": math.sqrt(rep / pob_s * 10000),          # per cápita
            "dano": math.sqrt(gravedad),                         # severidad per cápita
        }
        meta[clave] = {
            "estado": estado, "municipio": muni, "parroquia": parr,
            "poblacion": pob, "mmi": r.get("mmi"), "reportes": rep,
            "colapsadas": colaps, "desaparecidos": r.get("desaparecidos") or 0,
            "criticos": r.get("criticos") or 0,
            "sobrevivientes": a.get("sobrevivientes", 0),
            "sobrev_no_atendidos": a.get("sobrev_no_atendidos", 0),
            "rescate_urgente": a.get("rescate_urgente", 0),
            "ultimo_sobreviviente": a.get("ultimo_sobreviviente"),
        }

    # Normaliza cada factor 0–5 entre parroquias (incl. vertical, solo informativo).
    factores = ("intensidad", "densidad_pob", "vertical", "reportes", "dano")
    norm = {f: _minmax_0_5({k: crudos[k][f] for k in crudos}) for f in factores}

    # Compuesto ponderado (4 factores; vertical excluido) y reescalado 0–5 para
    # que la parroquia de mayor prioridad del conjunto = 5.0.
    compuesto = {k: sum(_PESOS[f] * norm[f][k] for f in _FACTORES_IPCT) for k in crudos}
    ipct_scaled = _minmax_0_5(compuesto)

    filas = []
    for clave in crudos:
        fnorm = {f: norm[f][clave] for f in factores}
        ipct = round(ipct_scaled[clave], 1)
        # Motivo principal = factor (de los que entran al IPCT) con mayor valor.
        motivo_f = max(_FACTORES_IPCT, key=lambda f: fnorm[f])
        filas.append({
            **meta[clave],
            "factores_0_5": fnorm,
            "ipct": ipct,
            "nivel": _nivel(ipct),
            "factor_dominante": motivo_f,
        })
    filas.sort(key=lambda x: x["ipct"], reverse=True)
    for i, f in enumerate(filas, 1):
        f["ranking"] = i
    return filas


_MOTIVO = {
    "intensidad": "alta intensidad sísmica (MMI)",
    "densidad_pob": "alta exposición poblacional",
    "vertical": "alta densidad de edificación vertical en riesgo",
    "reportes": "alta densidad de reportes ciudadanos",
    "dano": "alto volumen de daño estructural",
}


def ranking_ipct(top: int = 25) -> dict:
    """Hito 1: ranking de parroquias por IPCT (0–5)."""
    filas = _calcular()
    out = []
    for f in filas[: top or len(filas)]:
        out.append({
            "ranking": f["ranking"], "estado": f["estado"], "municipio": f["municipio"],
            "parroquia": f["parroquia"], "ipct": f["ipct"], "nivel": f["nivel"],
            "motivo_principal": _MOTIVO.get(f["factor_dominante"], ""),
            "poblacion": f["poblacion"], "mmi": f["mmi"], "reportes": f["reportes"],
            "danos_estructurales": f["colapsadas"], "desaparecidos": f["desaparecidos"],
            "factores_0_5": f["factores_0_5"],
        })
    return {
        "unidad": "parroquia (cuadrante donde exista; aún no hay capa de cuadrantes)",
        "escala": "0–5 (5 = máxima prioridad del conjunto analizado)",
        "ponderacion_v1": _PESOS,
        "factores": [
            "F1 intensidad sísmica (MMI)",
            "F2 densidad/exposición poblacional",
            "F4 densidad de reportes ciudadanos (per cápita)",
            "F5 daño estructural y afectación grave (colapsos×2 + desaparecidos×4 + críticos, per cápita)",
        ],
        "factor_pendiente": ("F3 construcción vertical: NO entra en el cálculo v1 (falta la capa "
                             "GIS de edificación vertical — Chumaceiro). Se muestra un proxy "
                             "informativo basado en reportes de edificios en riesgo."),
        "nota_limitaciones": ("Volumen medido PER CÁPITA (por 10.000 hab, suavizado +20.000) para "
                              "priorizar por gravedad relativa a la población, no por tamaño "
                              "absoluto. IPCT = convergencia ponderada de F1/F2/F4/F5 reescalada "
                              "0–5. Población estimada; reportes autodeclarados."),
        "total_parroquias": len(filas),
        "ranking": out,
    }


# --------------------------------------------------------------------------- #
# Hito 2 — Filtro de posibles sobrevivientes (ventana 72 h)
# --------------------------------------------------------------------------- #
def ranking_sobrevivientes(top: int = 25, min_no_atendidos: int = 1) -> dict:
    """Hito 2: zonas con reportes de posibles sobrevivientes NO atendidos, ordenadas
    por URGENCIA DE RESCATE (vidas en juego, en términos absolutos), no por IPCT
    per cápita — así no se entierran zonas grandes con muchos atrapados/desaparecidos
    (p. ej. Catia La Mar). El IPCT se muestra como contexto de criticidad."""
    filas = _calcular()
    ref_now = _agregados_parroquia()["ref_now"]
    evento = dt.datetime(2026, 6, 24, 0, 0)
    out = []
    for f in filas:
        if f["sobrev_no_atendidos"] < min_no_atendidos:
            continue
        ult = f.get("ultimo_sobreviviente")
        horas = round((ref_now - ult).total_seconds() / 3600, 1) if isinstance(ult, dt.datetime) else None
        horas_evento = round((ref_now - evento).total_seconds() / 3600, 1)
        out.append({
            "estado": f["estado"], "municipio": f["municipio"], "parroquia": f["parroquia"],
            "ipct": f["ipct"], "nivel": f["nivel"],
            "posibles_sobrevivientes": f["sobrevivientes"],
            "no_atendidos": f["sobrev_no_atendidos"],
            "rescate_urgente_no_atendido": f["rescate_urgente"],
            "desaparecidos": f["desaparecidos"],
            "ultimo_reporte": ult.isoformat(timespec="minutes") if isinstance(ult, dt.datetime) else None,
            "horas_desde_ultimo_reporte": horas,
            "dentro_ventana_72h": (horas_evento <= 96),  # ventana de rescate aún relevante
            "estado_atencion": "No verificado" if f["sobrev_no_atendidos"] else "Parcial",
            "accion_sugerida": ("Verificación y rescate inmediato" if f["rescate_urgente"]
                                else "Verificación territorial prioritaria"),
        })
    # Orden: urgencia de rescate = primero rescate urgente no atendido, luego total
    # no atendidos, luego IPCT como desempate.
    out.sort(key=lambda x: (x["rescate_urgente_no_atendido"], x["no_atendidos"], x["ipct"]),
             reverse=True)
    return {
        "criterio": "Parroquias con reportes de posibles sobrevivientes NO atendidos, ordenadas por urgencia de rescate (vidas en juego).",
        "ventana_critica": "Rescate con vida 72–96 h desde el 24-jun-2026 (INSARAG).",
        "referencia_temporal": ref_now.isoformat(timespec="minutes"),
        "ranking": out[: top or len(out)],
    }

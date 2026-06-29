"""Capa de datos del evento Terremoto 24J.

TODAS las consultas/agregaciones que un comité de crisis necesita, devolviendo
JSON limpio y serializable. Es la fuente de verdad cuantitativa que consume el
agente. Toda función construye su query con `build_event_query(...)` (paso 02).

Manejo de PII: `include_pii=False` por defecto en TODO. Solo si quien llama lo
activa explícitamente (uso oficial) se devuelve PII.
"""
from __future__ import annotations

import datetime as dt
import re
from typing import Any

from bson import ObjectId

from app.config import VEN_BBOX
from app.db.mongo import build_event_query, get_reports_collection

TZ = "America/Caracas"  # UTC-4, para agrupaciones temporales

# Campos PII autodeclarados (uso oficial restringido).
_PII_FIELDS = ("displayName", "dni", "phone_number", "email")

# Patrones de detección (regex, insensible a mayúsculas).
RE_DESAPARECIDOS = re.compile(r"desaparec|no aparece|no localiza|paradero", re.IGNORECASE)
RE_DANO = re.compile(
    r"estructural|colaps|derrumb|grieta|agriet|fisura|fractur|punto de caer|riesgo de colapso",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------- #
# Serialización / PII
# --------------------------------------------------------------------------- #
def _jsonify(value: Any) -> Any:
    """Convierte recursivamente datetime->ISO y ObjectId->str."""
    if isinstance(value, dict):
        return {k: _jsonify(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonify(v) for v in value]
    if isinstance(value, dt.datetime):
        return value.isoformat()
    if isinstance(value, ObjectId):
        return str(value)
    return value


def redactar(doc: dict) -> dict:
    """Redacta PII: reemplaza displayName/dni/phone_number/email por [REDACTADO]
    y recorta `address` a municipio/parroquia cuando es posible."""
    d = dict(doc)
    for f in _PII_FIELDS:
        if f in d and d[f] not in (None, ""):
            d[f] = "[REDACTADO]"
    if d.get("address"):
        muni = (d.get("municipality") or {}).get("name") if isinstance(d.get("municipality"), dict) else None
        parr = (d.get("parroquia") or {}).get("name") if isinstance(d.get("parroquia"), dict) else None
        partes = [p for p in (parr, muni) if p]
        d["address"] = ", ".join(partes) if partes else "[REDACTADO]"
    return d


def _proyeccion_reporte() -> dict:
    return {
        "number": 1, "createdAt": 1, "status": 1, "title": 1, "description": 1,
        "extracategory.name": 1, "subcategory.name": 1, "additionalcategory.name": 1,
        "province.name": 1, "municipality.name": 1, "parroquia.name": 1,
        "address": 1, "assignedTo": 1, "location.coordinates": 1,
        "latitude": 1, "longitude": 1,
        # PII (se redacta salvo include_pii=True).
        "displayName": 1, "dni": 1, "phone_number": 1, "email": 1,
    }


def _clean_report(doc: dict, include_pii: bool) -> dict:
    doc = _jsonify(doc)
    if not include_pii:
        doc = redactar(doc)
    return doc


def _col():
    return get_reports_collection()


# --------------------------------------------------------------------------- #
# 1. Total
# --------------------------------------------------------------------------- #
def total_reportes(**f) -> int:
    return _col().count_documents(build_event_query(**f))


# --------------------------------------------------------------------------- #
# 2. Por estado de gestión (status)
# --------------------------------------------------------------------------- #
def por_status(**f) -> list[dict]:
    q = build_event_query(**f)
    total = _col().count_documents(q) or 1
    pipeline = [
        {"$match": q},
        {"$group": {"_id": "$status", "conteo": {"$sum": 1}}},
        {"$sort": {"conteo": -1}},
    ]
    out = []
    for r in _col().aggregate(pipeline):
        status = r["_id"] or "Sin estado"
        out.append({
            "status": status,
            "conteo": r["conteo"],
            "porcentaje": round(100 * r["conteo"] / total, 1),
            "resuelto": status == "Atendido",
        })
    return out


# --------------------------------------------------------------------------- #
# Helper genérico de agrupación por campo
# --------------------------------------------------------------------------- #
def _group_by(field: str, label: str, top: int, extra_field: str | None = None, **f) -> list[dict]:
    q = build_event_query(**f)
    group: dict = {"_id": f"${field}", "conteo": {"$sum": 1}}
    if extra_field:
        group[extra_field.replace(".", "_")] = {"$first": f"${extra_field}"}
    pipeline = [
        {"$match": q},
        {"$group": group},
        {"$sort": {"conteo": -1}},
        {"$limit": top},
    ]
    out = []
    for r in _col().aggregate(pipeline):
        item = {label: r["_id"] or "Sin dato", "conteo": r["conteo"]}
        if extra_field:
            item[extra_field.replace(".", "_")] = r.get(extra_field.replace(".", "_")) or "Sin dato"
        out.append(item)
    return out


# 3. Por extracategoría (tipo de emergencia)
def por_extracategoria(top: int = 20, **f) -> list[dict]:
    return _group_by("extracategory.name", "extracategoria", top, **f)


# 4. Por subcategoría
def por_subcategoria(top: int = 20, **f) -> list[dict]:
    return _group_by("subcategory.name", "subcategoria", top, **f)


# 5. Por estado geográfico (provincia)
def por_estado_geografico(top: int = 30, **f) -> list[dict]:
    return _group_by("province.name", "estado", top, **f)


# 6. Por municipio (con provincia para contexto)
def por_municipio(top: int = 30, **f) -> list[dict]:
    return _group_by("municipality.name", "municipio", top, extra_field="province.name", **f)


# --------------------------------------------------------------------------- #
# 7. Evolución temporal
# --------------------------------------------------------------------------- #
def evolucion_temporal(granularidad: str = "dia", **f) -> list[dict]:
    q = build_event_query(**f)
    fmt = "%Y-%m-%d" if granularidad == "dia" else "%Y-%m-%d %H:00"
    pipeline = [
        {"$match": q},
        {"$group": {
            "_id": {"$dateToString": {"format": fmt, "date": "$createdAt", "timezone": TZ}},
            "conteo": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]
    return [{"periodo": r["_id"], "conteo": r["conteo"]} for r in _col().aggregate(pipeline)]


# Agrupación de subcategorías en "tipos de afectación" legibles para la tendencia.
_TIPOS_AFECTACION: dict[str, list[str]] = {
    "Edificaciones afectadas": ["Vivienda y edificaciones",
                                "Hospitales, escuelas y edificios públicos"],
    "Personas": ["Personas"],
    "Servicios": ["Electricidad, agua, gas y telecomunicaciones"],
}


def evolucion_por_tipo(**f) -> dict:
    """Evolución DIARIA desde el evento: total de reportes y desglose por grandes
    tipos de afectación (edificaciones, personas, servicios). Pensado para graficar
    la tendencia 'desde el 24J por día'. Devuelve {periodos, series:{nombre:[...]}}.
    """
    total = evolucion_temporal(granularidad="dia", **f)
    periodos = [r["periodo"] for r in total]
    series: dict[str, list[int]] = {"Total reportes": [r["conteo"] for r in total]}
    for etiqueta, subs in _TIPOS_AFECTACION.items():
        acc = {p: 0 for p in periodos}
        for sub in subs:
            pipeline = [
                {"$match": {**build_event_query(**f), "subcategory.name": sub}},
                {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d",
                                                      "date": "$createdAt", "timezone": TZ}},
                            "conteo": {"$sum": 1}}},
            ]
            for r in _col().aggregate(pipeline):
                if r["_id"] in acc:
                    acc[r["_id"]] += r["conteo"]
        series[etiqueta] = [acc[p] for p in periodos]
    return {"periodos": periodos, "series": series}


# --------------------------------------------------------------------------- #
# Estadísticas de infraestructura DERIVADAS DE LOS DATOS (para gráficos)
# --------------------------------------------------------------------------- #
# Detección por palabras clave en título/descripción. Reemplaza el viejo método
# (rascar cifras de la prosa del LLM), que dejaba de funcionar al cambiar la
# redacción. NOTA: el "estado operativo" de hospitales (operativo/campaña/dañado)
# NO es un campo del origen; por eso la sección de salud se grafica como desglose
# de reportes en edificios públicos (salud/educación/otros), que sí está en datos.
_RX_INFRA = {
    "el_cortes": r"corte|apag[oó]n|sin luz|sin electricidad|sin (el|la) (corriente|servicio el[eé]ctrico)",
    "el_cables": r"cable",
    "el_postes": r"poste",
    "el_trafo": r"transformador",
    "sec_agua": r"\bagua|tuber[ií]a|acueducto|cloaca|aguas (blancas|negras|servidas)|filtraci[oó]n",
    "sec_gas": r"\bgas\b|bombona|fuga de gas",
    "sec_telecom": r"internet|tel[eé]fon|se[ñn]al|cantv|telecomunicaci|fibra[ ]?[oó]ptica",
}
_RX_SALUD = re.compile(r"hospital|cl[ií]nica|ambulatorio|\bcdi\b|centro de salud|maternidad|dispensario", re.I)
_RX_EDU = re.compile(r"escuela|colegio|liceo|universidad|preescolar|\bu\.?e\.?\b|bolivariano|instituto", re.I)


def _cnt_kw(pattern: str, **f) -> int:
    rx = {"$regex": pattern, "$options": "i"}
    q = build_event_query(**f)
    return _col().count_documents({**q, "$or": [{"title": rx}, {"description": rx}]})


def estadisticas_infraestructura(**f) -> dict:
    """Stats de infraestructura para los gráficos, DERIVADAS DE LOS DATOS (keyword
    en título/descripción). Mismas claves que consume `charts.graficos_infraestructura`:
    electricidad (por tipo), gas, agua, telecom y salud (edificios públicos por tipo).
    """
    el = {k: v for k, v in {
        "Cortes / apagón": _cnt_kw(_RX_INFRA["el_cortes"], **f),
        "Cables": _cnt_kw(_RX_INFRA["el_cables"], **f),
        "Postes": _cnt_kw(_RX_INFRA["el_postes"], **f),
        "Transformadores": _cnt_kw(_RX_INFRA["el_trafo"], **f),
    }.items() if v}

    stats: dict = {}
    if el:
        stats["electricidad"] = el
    if (v := _cnt_kw(_RX_INFRA["sec_gas"], **f)):
        stats["gas"] = {"Incidencias de gas": v}
    if (v := _cnt_kw(_RX_INFRA["sec_agua"], **f)):
        stats["agua"] = {"Agua y saneamiento": v}
    if (v := _cnt_kw(_RX_INFRA["sec_telecom"], **f)):
        stats["telecom"] = {"Telecomunicaciones": v}

    # Salud / educación / edificios públicos: clasifica los reportes de esa
    # subcategoría (cada doc en UNA categoría, sin doble conteo).
    sub_pub = {"subcategory.name": "Hospitales, escuelas y edificios públicos"}
    salud = {"Salud (hospitales/clínicas)": 0, "Educación (escuelas/liceos)": 0,
             "Otros edificios públicos": 0}
    for d in _col().find({**build_event_query(**f), **sub_pub}, {"title": 1, "description": 1}):
        txt = f"{d.get('title') or ''} {d.get('description') or ''}"
        if _RX_SALUD.search(txt):
            salud["Salud (hospitales/clínicas)"] += 1
        elif _RX_EDU.search(txt):
            salud["Educación (escuelas/liceos)"] += 1
        else:
            salud["Otros edificios públicos"] += 1
    if sum(salud.values()):
        stats["salud"] = salud
    return stats


# --------------------------------------------------------------------------- #
# 8. Cobertura de asignación
# --------------------------------------------------------------------------- #
def cobertura_asignacion(**f) -> dict:
    q = build_event_query(**f)
    total = _col().count_documents(q)
    asignados = _col().count_documents({**q, "assignedTo": {"$nin": [None, ""]}})
    manuales = _col().count_documents({**q, "sentManually": True})
    pct = round(100 * asignados / total, 1) if total else 0.0
    return {
        "total": total,
        "asignados": asignados,
        "sin_asignar": total - asignados,
        "porcentaje_asignados": pct,
        "enviados_manualmente": manuales,
    }


# --------------------------------------------------------------------------- #
# Helper de detección por keywords + categorías
# --------------------------------------------------------------------------- #
def _match_keywords(regex: re.Pattern, **f) -> dict:
    q = build_event_query(**f)
    return {
        **q,
        "$or": [
            {"title": {"$regex": regex.pattern, "$options": "i"}},
            {"description": {"$regex": regex.pattern, "$options": "i"}},
            {"extracategory.name": {"$regex": regex.pattern, "$options": "i"}},
            {"subcategory.name": {"$regex": regex.pattern, "$options": "i"}},
        ],
    }


def _detalle_focalizado(regex: re.Pattern, limit: int, **f) -> dict:
    q = _match_keywords(regex, **f)
    conteo = _col().count_documents(q)
    por_estado = list(_col().aggregate([
        {"$match": q},
        {"$group": {"_id": "$province.name", "conteo": {"$sum": 1}}},
        {"$sort": {"conteo": -1}},
        {"$limit": 30},
    ]))
    por_estado = [{"estado": r["_id"] or "Sin dato", "conteo": r["conteo"]} for r in por_estado]
    muestra = [
        _clean_report(d, include_pii=False)
        for d in _col().find(q, _proyeccion_reporte()).sort("createdAt", -1).limit(limit)
    ]
    return {"conteo": conteo, "por_estado": por_estado, "muestra": muestra}


# 9. Desaparecidos
def desaparecidos(limit: int = 15, **f) -> dict:
    return _detalle_focalizado(RE_DESAPARECIDOS, limit, **f)


# 10. Daño estructural
def dano_estructural(limit: int = 15, **f) -> dict:
    return _detalle_focalizado(RE_DANO, limit, **f)


# --------------------------------------------------------------------------- #
# 11. Puntos geográficos (validados contra el bounding box de Venezuela)
# --------------------------------------------------------------------------- #
def _in_bbox(lat, lng) -> bool:
    try:
        lat = float(lat); lng = float(lng)
    except (TypeError, ValueError):
        return False
    return (VEN_BBOX["lat_min"] <= lat <= VEN_BBOX["lat_max"]
            and VEN_BBOX["lng_min"] <= lng <= VEN_BBOX["lng_max"])


def puntos_geo(limit: int = 2000, **f) -> list[dict]:
    q = build_event_query(**f)
    proj = {
        "location.coordinates": 1, "latitude": 1, "longitude": 1,
        "extracategory.name": 1, "province.name": 1,
    }
    out: list[dict] = []
    for d in _col().find(q, proj).limit(limit):
        lat = lng = None
        coords = (d.get("location") or {}).get("coordinates") if isinstance(d.get("location"), dict) else None
        if isinstance(coords, (list, tuple)) and len(coords) == 2:
            lng, lat = coords[0], coords[1]  # GeoJSON: [lng, lat]
        if lat is None or lng is None:
            lat, lng = d.get("latitude"), d.get("longitude")
        if not _in_bbox(lat, lng):
            continue
        out.append({
            "lat": float(lat), "lng": float(lng),
            "extracategoria": (d.get("extracategory") or {}).get("name") if isinstance(d.get("extracategory"), dict) else None,
            "estado": (d.get("province") or {}).get("name") if isinstance(d.get("province"), dict) else None,
        })
    return out


# --------------------------------------------------------------------------- #
# 12. Muestra de reportes
# --------------------------------------------------------------------------- #
def muestra_reportes(focus: str | None = None, limit: int = 20,
                     include_pii: bool = False, **f) -> list[dict]:
    """Muestra de reportes con proyección útil. focus: 'desaparecidos',
    'dano_estructural' o 'general'. PII redactada salvo include_pii=True."""
    if focus == "desaparecidos":
        q = _match_keywords(RE_DESAPARECIDOS, **f)
    elif focus == "dano_estructural":
        q = _match_keywords(RE_DANO, **f)
    else:
        q = build_event_query(**f)
    cursor = _col().find(q, _proyeccion_reporte()).sort("createdAt", -1).limit(limit)
    return [_clean_report(d, include_pii=include_pii) for d in cursor]


# --------------------------------------------------------------------------- #
# 13. Panorama completo (payload principal del agente)
# --------------------------------------------------------------------------- #
def panorama_completo(**f) -> dict:
    return {
        "evento": "Terremoto 24J — Venezuela",
        "total": total_reportes(**f),
        "por_status": por_status(**f),
        "por_extracategoria": por_extracategoria(top=20, **f),
        "por_subcategoria": por_subcategoria(top=15, **f),
        "por_estado_geografico": por_estado_geografico(top=30, **f),
        "por_municipio": por_municipio(top=30, **f),
        "evolucion_temporal": evolucion_temporal(granularidad="dia", **f),
        "evolucion_por_tipo": evolucion_por_tipo(**f),
        # NOTA: la cobertura de asignación (assignedTo) NO se incluye: ese campo
        # aún no se está guardando de forma consistente en el origen, así que como
        # indicador genera ruido. Ver `cobertura_asignacion` (queda disponible
        # para diagnóstico, pero fuera del payload del informe).
        "desaparecidos": desaparecidos(limit=10, **f),
        "dano_estructural": dano_estructural(limit=10, **f),
        "puntos_geo_resumen": {
            "total_validos": len(puntos_geo(limit=2000, **f)),
        },
    }


# --------------------------------------------------------------------------- #
# 14. Listar estados (para el dropdown del frontend)
# --------------------------------------------------------------------------- #
def listar_estados(**f) -> list[str]:
    valores = _col().distinct("province.name", build_event_query(**f))
    return sorted([v for v in valores if v])

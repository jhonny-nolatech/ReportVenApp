"""Clasificador de reportes por IA — edificios derrumbados / en riesgo (Terremoto 24J).

Resuelve el sesgo de fondo (pedido de Yeickson): los reportes NO traen un campo que
diga si lo afectado es un EDIFICIO derrumbado, una vivienda, o algo en riesgo de
colapso; ni el ESTADO REAL del hecho (un reporte puede "denunciarse desde Caracas"
pero referirse a otro estado). Aquí la IA LEE título + descripción de cada reporte y
clasifica:

  - tipo: 'derrumbado' (edificación colapsada) | 'riesgo' (en riesgo de colapso) |
          'vivienda' (casa unifamiliar dañada) | 'otro' (no es daño estructural).
  - vertical: True si es edificio/torre/multifamiliar; False si vivienda unifamiliar.
  - estado_real: el estado venezolano del HECHO inferido del texto (corrige el sesgo
                 de "denunciado desde Caracas"); None si el texto no lo aclara.

Diseño: DETERMINISTA-cacheado. Cada reporte se clasifica UNA vez y se guarda en
`cache_clasificacion_edificios.json` (gitignored). Reejecutar es incremental: solo
clasifica lo nuevo. Para edificios cuenta tanto reportes como edificios DISTINTOS
(dedup por coordenadas ~11 m), porque varios vecinos reportan el mismo edificio.

Solo lectura sobre los reportes; el caché no guarda PII (cédula/teléfono/email).
"""
from __future__ import annotations

import json
import os
import re

from app.config import Settings
from app.db.mongo import build_event_query, get_reports_collection

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE_PATH = os.path.join(_ROOT, "cache_clasificacion_edificios.json")

# Modelo barato y rápido para clasificar a escala (15k+ filas). Configurable por env.
MODELO_CLASIFICADOR = os.environ.get("ANTHROPIC_MODEL_CLASIFICADOR", "claude-haiku-4-5-20251001")
_BATCH = 40
_DESC_MAX = 280

_TIPOS = {"derrumbado", "riesgo", "vivienda", "otro"}

_SYSTEM = (
    "Eres un clasificador experto de reportes de daños del Terremoto 24J (Venezuela). "
    "Para cada reporte, leyendo SOLO su título y descripción, devuelves su clasificación. "
    "Responde EXCLUSIVAMENTE con un array JSON, un objeto por reporte, sin texto extra.\n"
    "Cada objeto: {\"i\": <indice>, \"tipo\": \"derrumbado|riesgo|vivienda|otro\", "
    "\"vertical\": true|false, \"estado_real\": \"<estado venezolano>\"|null}.\n"
    "Definiciones:\n"
    "- tipo 'derrumbado': la edificación COLAPSÓ/se derrumbó/quedó destruida (ya ocurrió).\n"
    "- tipo 'riesgo': edificación EN RIESGO de colapso (agrietada, ladeada, paredes a punto "
    "de caer, evacuada por peligro) pero que AÚN NO colapsó.\n"
    "- tipo 'vivienda': daño en vivienda unifamiliar (casa/rancho), no edificio.\n"
    "- tipo 'otro': no es daño estructural de edificación (servicios, personas, etc.).\n"
    "- vertical: true si es EDIFICIO/torre/residencias/multifamiliar/varios pisos; false si casa.\n"
    "- estado_real: el estado de Venezuela donde OCURRIÓ el hecho según el texto (p. ej. la "
    "dirección o lugar mencionado). Si el texto no menciona un lugar que permita inferirlo, "
    "devuelve null (se usará el estado declarado). OJO: el lugar del hecho puede diferir del "
    "estado declarado."
)


# --------------------------------------------------------------------------- #
# Lectura de reportes y caché
# --------------------------------------------------------------------------- #
def _reportes(limite: int | None = None) -> list[dict]:
    col = get_reports_collection()
    proj = {"number": 1, "title": 1, "description": 1, "province.name": 1,
            "latitude": 1, "longitude": 1}
    out = []
    for d in col.find(build_event_query(), proj):
        out.append({
            "numero": d.get("number") or "",
            "estado_decl": (d.get("province") or {}).get("name") if isinstance(d.get("province"), dict) else None,
            "titulo": d.get("title") or "",
            "descripcion": d.get("description") or "",
            "lat": d.get("latitude"), "lng": d.get("longitude"),
        })
        if limite and len(out) >= limite:
            break
    return out


def _cargar_cache() -> dict:
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:  # noqa: BLE001
            return {}
    return {}


def _guardar_cache(cache: dict) -> None:
    with open(CACHE_PATH, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, ensure_ascii=False)


# --------------------------------------------------------------------------- #
# Clasificación por IA (en lotes)
# --------------------------------------------------------------------------- #
def _parse_json_array(texto: str) -> list[dict]:
    s = texto.strip()
    s = re.sub(r"^```(json)?|```$", "", s, flags=re.MULTILINE).strip()
    m = re.search(r"\[.*\]", s, re.DOTALL)
    if m:
        s = m.group(0)
    try:
        data = json.loads(s)
        return data if isinstance(data, list) else []
    except Exception:  # noqa: BLE001
        return []


def _clasificar_lote(client, modelo: str, lote: list[dict]) -> dict[int, dict]:
    lineas = []
    for i, r in enumerate(lote):
        desc = (r["descripcion"] or "")[:_DESC_MAX].replace("\n", " ")
        lineas.append(f'{i}. [estado declarado: {r["estado_decl"] or "?"}] '
                      f'Título: {r["titulo"][:120]} | Desc: {desc}')
    user = "Clasifica estos reportes:\n" + "\n".join(lineas)
    msg = client.messages.create(
        model=modelo, max_tokens=4096, system=_SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    texto = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    out: dict[int, dict] = {}
    for obj in _parse_json_array(texto):
        try:
            i = int(obj.get("i"))
        except (TypeError, ValueError):
            continue
        tipo = str(obj.get("tipo", "otro")).lower()
        if tipo not in _TIPOS:
            tipo = "otro"
        out[i] = {
            "tipo": tipo,
            "vertical": bool(obj.get("vertical", False)),
            "estado_real": obj.get("estado_real") or None,
        }
    return out


def clasificar(modelo: str | None = None, batch: int = _BATCH,
               limite: int | None = None, refrescar: bool = False,
               progreso=print) -> dict:
    """Clasifica los reportes del evento (incremental con caché). Devuelve el caché
    {numero: {tipo, vertical, estado_real, estado_decl, lat, lng}}."""
    from anthropic import Anthropic
    s = Settings()
    if not s.anthropic_api_key:
        raise RuntimeError("Falta ANTHROPIC_API_KEY para clasificar.")
    modelo = modelo or MODELO_CLASIFICADOR
    client = Anthropic(api_key=s.anthropic_api_key)

    reportes = _reportes(limite=limite)
    cache = {} if refrescar else _cargar_cache()
    pendientes = [r for r in reportes if r["numero"] and r["numero"] not in cache]
    if progreso:
        progreso(f"Reportes: {len(reportes)} | ya en caché: {len(reportes) - len(pendientes)} | "
                 f"a clasificar: {len(pendientes)} (modelo {modelo})")

    for ini in range(0, len(pendientes), batch):
        lote = pendientes[ini:ini + batch]
        try:
            res = _clasificar_lote(client, modelo, lote)
        except Exception as e:  # noqa: BLE001
            if progreso:
                progreso(f"  ⚠️ error en lote {ini}-{ini+len(lote)}: {e}")
            continue
        for i, r in enumerate(lote):
            c = res.get(i)
            if not c:
                continue
            cache[r["numero"]] = {**c, "estado_decl": r["estado_decl"],
                                  "lat": r["lat"], "lng": r["lng"]}
        _guardar_cache(cache)  # guardado incremental (resumible)
        if progreso:
            progreso(f"  {min(ini + batch, len(pendientes))}/{len(pendientes)} clasificados…")
    return cache


# --------------------------------------------------------------------------- #
# Agregados por estado (con dedup de edificios por coordenadas)
# --------------------------------------------------------------------------- #
# Canonicaliza nombres de estado que la IA puede devolver con variantes/nombres
# viejos, para no partir el conteo (p. ej. 'Vargas' = nombre antiguo de 'La Guaira').
_CANON_ESTADO = {
    "vargas": "La Guaira",
    "la guaira": "La Guaira",
    "distrito capital": "Caracas",
    "dtto capital": "Caracas",
    "distrito metropolitano": "Caracas",
    "caracas": "Caracas",
}


def _canon_estado(nombre: str | None) -> str | None:
    if not nombre:
        return None
    s = str(nombre).strip()
    return _CANON_ESTADO.get(s.lower(), s)


def _estado_efectivo(rec: dict) -> str:
    return (_canon_estado(rec.get("estado_real"))
            or _canon_estado(rec.get("estado_decl")) or "Sin dato")


_CAMPO = {
    ("edificios", "derrumbado"): "edificios_derrumbados",
    ("edificios", "riesgo"): "edificios_riesgo",
    ("viviendas", "derrumbado"): "viviendas_derrumbadas",
    ("viviendas", "riesgo"): "viviendas_riesgo",
}


def agregados(cache: dict | None = None) -> dict:
    """Agrega el caché por estado REAL: edificaciones (VERTICALES) y viviendas
    (HORIZONTALES) derrumbadas / en riesgo, deduplicando por coordenadas (~11 m)."""
    cache = cache if cache is not None else _cargar_cache()
    base = {"edificios_derrumbados": 0, "edificios_riesgo": 0,
            "viviendas_derrumbadas": 0, "viviendas_riesgo": 0}
    por_estado: dict[str, dict] = {}
    coords_vistas: dict[tuple, set] = {}
    for rec in cache.values():
        tipo = rec.get("tipo")
        if tipo not in ("derrumbado", "riesgo"):
            continue
        est = _estado_efectivo(rec)
        cat = "edificios" if rec.get("vertical") else "viviendas"
        campo = _CAMPO[(cat, tipo)]
        e = por_estado.setdefault(est, dict(base))
        lat, lng = rec.get("lat"), rec.get("lng")
        if lat and lng:
            key = (est, cat, tipo)
            s = coords_vistas.setdefault(key, set())
            c = (round(float(lat), 4), round(float(lng), 4))
            if c in s:
                continue  # mismo edificio/vivienda ya contado
            s.add(c)
        e[campo] += 1
    return por_estado


def flujos_sesgo(top: int = 12) -> dict:
    """Cuantifica el sesgo: reportes cuyo estado REAL (inferido del texto) difiere del
    DECLARADO. Devuelve total, % y los principales flujos 'declarado → real'."""
    cache = _cargar_cache()
    flujos: dict[str, int] = {}
    recl = total = 0
    hacia: dict[str, int] = {}
    for rec in cache.values():
        real = _canon_estado(rec.get("estado_real"))
        decl = _canon_estado(rec.get("estado_decl"))
        if not real:
            continue
        total += 1
        if decl and real != decl:
            recl += 1
            flujos[f"{decl} → {real}"] = flujos.get(f"{decl} → {real}", 0) + 1
            hacia[real] = hacia.get(real, 0) + 1
    top_flujos = sorted(flujos.items(), key=lambda x: x[1], reverse=True)[:top]
    return {
        "reclasificados": recl, "con_estado_real": total,
        "pct": round(100 * recl / total, 1) if total else 0.0,
        "flujos": [{"flujo": k, "conteo": v} for k, v in top_flujos],
        "hacia_estado": sorted(hacia.items(), key=lambda x: x[1], reverse=True),
    }


def composicion(cache: dict | None = None) -> dict:
    """Composición de los reportes por tipo (derrumbado/riesgo/vivienda/otro)."""
    cache = cache if cache is not None else _cargar_cache()
    tipos: dict[str, int] = {}
    for rec in cache.values():
        t = rec.get("tipo") or "otro"
        tipos[t] = tipos.get(t, 0) + 1
    etiquetas = {"derrumbado": "Edificación derrumbada", "riesgo": "En riesgo de colapso",
                 "vivienda": "Vivienda dañada", "otro": "Otros (servicios/personas)"}
    return {etiquetas.get(k, k): v for k, v in tipos.items()}


def resumen(aptos_promedio: int = 100, personas_hogar: int = 6,
            cache: dict | None = None) -> dict:
    """Totales para el documento: por estado y agregados de personas a REUBICAR
    (en edificios derrumbados + viviendas derrumbadas) y PRÓXIMAS a reubicar (en
    riesgo de colapso). Vertical: edificios × aptos × personas. Horizontal: viviendas
    × personas (1 hogar). Todo con edificaciones DISTINTAS (deduplicadas)."""
    por_estado = agregados(cache)
    f_edif = max(1, int(aptos_promedio)) * max(1, int(personas_hogar))  # personas por edificio
    f_viv = max(1, int(personas_hogar))                                  # personas por vivienda
    filas = []
    tot = {"edif_d": 0, "edif_r": 0, "viv_d": 0, "viv_r": 0, "reubicar": 0, "proximos": 0}
    for est, e in por_estado.items():
        ed, er = e["edificios_derrumbados"], e["edificios_riesgo"]
        vd, vr = e["viviendas_derrumbadas"], e["viviendas_riesgo"]
        a_reubicar = ed * f_edif + vd * f_viv
        proximos = er * f_edif + vr * f_viv
        tot["edif_d"] += ed; tot["edif_r"] += er; tot["viv_d"] += vd; tot["viv_r"] += vr
        tot["reubicar"] += a_reubicar; tot["proximos"] += proximos
        filas.append({
            "estado": est,
            "edificios_derrumbados": ed, "edificios_riesgo": er,
            "viviendas_derrumbadas": vd, "viviendas_riesgo": vr,
            "personas_a_reubicar": a_reubicar,
            "personas_proximas_reubicar": proximos,
        })
    filas.sort(key=lambda x: x["personas_a_reubicar"], reverse=True)
    return {
        "aptos_promedio": aptos_promedio, "personas_hogar": personas_hogar,
        "total_edificios_derrumbados": tot["edif_d"], "total_edificios_riesgo": tot["edif_r"],
        "total_viviendas_derrumbadas": tot["viv_d"], "total_viviendas_riesgo": tot["viv_r"],
        "total_a_reubicar": tot["reubicar"],
        "total_proximos_reubicar": tot["proximos"],
        "por_estado": filas,
        "clasificados": len(cache if cache is not None else _cargar_cache()),
    }


def cobertura() -> float:
    """Fracción de reportes del evento ya clasificados (0–1)."""
    cache = _cargar_cache()
    if not cache:
        return 0.0
    try:
        total = get_reports_collection().count_documents(build_event_query())
    except Exception:  # noqa: BLE001
        return 1.0  # sin BD para contar: asumimos completo
    return (len(cache) / total) if total else 0.0


def disponible(min_cobertura: float = 0.8) -> bool:
    """True solo si hay clasificación con cobertura SUFICIENTE (por defecto ≥80%).
    Evita que una corrida parcial/de prueba contamine el informe con datos
    incompletos."""
    return os.path.exists(CACHE_PATH) and cobertura() >= min_cobertura

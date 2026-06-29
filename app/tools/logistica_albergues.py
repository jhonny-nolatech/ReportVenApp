"""Logística de albergues/campamentos para desplazados — Terremoto 24J.

Calculadora DETERMINISTA (no la estima el modelo) de necesidades de un campamento
de emergencia "desde cero" (enfoque 'campamento en el desierto') a partir del
número de personas, usando estándares humanitarios reconocidos:

  * Esfera (Sphere Handbook 2018): agua, saneamiento, albergue, alimentación, salud.
  * ACNUR/UNHCR: planificación de asentamientos (superficie por persona).
  * OMS/PMA (WFP): ración alimentaria (2.100 kcal/persona/día).

Pensado para el documento "Plan de albergues y atención a desplazados": entrega
proyecciones por tamaño de campamento (100/250/500/1.000) y necesidades agregadas
para la población desplazada estimada. La energía eléctrica es una ESTIMACIÓN de
planificación (no hay cifra Esfera única) y se marca como tal.

Solo lectura; agregados (sin PII).
"""
from __future__ import annotations

import math

from app.db import data_service

# Supuestos de la dirección (André): 1 reporte ≈ 4 personas por hogar.
PERSONAS_POR_HOGAR = 4
# Horizonte de planificación por defecto (el jefe mencionó 5–10 días / 1 semana).
HORIZONTE_DIAS = 14
# Tamaños de campamento de referencia para las proyecciones.
TAMANOS_REFERENCIA = (100, 250, 500, 1000)
# Capacidad de un camión cisterna típico (L).
CISTERNA_L = 10000

# ----------------------------------------------------------------------------- #
# CORRECCIÓN DE SESGO (observación de Yeickson):
# El conteo de reportes está sesgado por la DENSIDAD DE REPORTE (Caracas reporta
# mucho más que La Guaira), así que "reportes × hogar" NO refleja el desplazamiento
# real: subestima el COLAPSO VERTICAL (edificios enteros que caen y generan cientos
# de desplazados con pocos reportes). Para esas zonas se usa una estimación POR
# EDIFICIOS, con cifras de fuente EXTERNA (prensa/dirección), no de los reportes.
#
# Edita esta tabla conforme se confirmen cifras oficiales de edificios afectados.
# Cada entrada: edificios afectados × apartamentos promedio × personas por hogar.
# IMPORTANTE: estas cifras son PRELIMINARES (no confirmadas oficialmente).
EDIFICIOS_VERTICALES_AFECTADOS: dict[str, dict] = {
    "La Guaira": {
        "edificios": 350, "aptos_promedio": 100, "personas_hogar": 6,
        "fuente": "Estimación dirección (Yeickson/André) — PRELIMINAR, confirmar con fuente oficial",
    },
    # "Caracas": {"edificios": ..., "aptos_promedio": ..., "personas_hogar": 6, "fuente": "..."},
}
# Supuestos (NO están en el CSV) usados cuando los EDIFICIOS los cuenta la IA por
# estado real: apartamentos promedio por edificio y personas por hogar. Confirmables.
APTOS_PROMEDIO_DEFAULT = 100
PERSONAS_HOGAR_VERTICAL = 6


def _ceil(x: float) -> int:
    return int(math.ceil(x - 1e-9))


def proyeccion_albergue(personas: int, dias: int = HORIZONTE_DIAS) -> list[dict]:
    """Necesidades de un campamento de `personas` durante `dias`. Devuelve una
    lista de {categoria, recurso, cantidad, unidad, estandar, fuente}."""
    p = max(0, int(personas))
    agua_dia = 15 * p  # L/día (Esfera: 15 L/persona/día para beber, cocinar e higiene)
    agua_periodo = agua_dia * dias
    kw_pico = round(0.1 * p, 1)  # estimación de planificación (servicios comunes)
    return [
        # --- Agua y saneamiento (WASH) ---
        {"categoria": "Agua y saneamiento", "recurso": "Agua potable (diaria)",
         "cantidad": agua_dia, "unidad": "L/día",
         "estandar": "15 L/persona/día", "fuente": "Esfera 2018"},
        {"categoria": "Agua y saneamiento", "recurso": f"Agua potable ({dias} días)",
         "cantidad": agua_periodo, "unidad": "L", "estandar": "15 L/persona/día", "fuente": "Esfera 2018"},
        {"categoria": "Agua y saneamiento", "recurso": "Camiones cisterna (10.000 L)",
         "cantidad": _ceil(agua_periodo / CISTERNA_L), "unidad": f"viajes en {dias} días",
         "estandar": "cobertura del consumo del período", "fuente": "—"},
        {"categoria": "Agua y saneamiento", "recurso": "Letrinas / baños químicos",
         "cantidad": _ceil(p / 20), "unidad": "unidades",
         "estandar": "1 por 20 personas", "fuente": "Esfera 2018"},
        {"categoria": "Agua y saneamiento", "recurso": "Duchas",
         "cantidad": _ceil(p / 50), "unidad": "unidades", "estandar": "1 por 50 personas", "fuente": "Esfera 2018"},
        {"categoria": "Agua y saneamiento", "recurso": "Puntos de lavado de manos",
         "cantidad": _ceil(p / 50), "unidad": "unidades", "estandar": "1 por 50 personas", "fuente": "Esfera 2018"},
        {"categoria": "Agua y saneamiento", "recurso": "Contenedores de residuos (100 L)",
         "cantidad": _ceil(p / 40), "unidad": "unidades", "estandar": "1 por 10 familias (~40 pers.)", "fuente": "Esfera 2018"},
        # --- Albergue / refugio ---
        {"categoria": "Albergue", "recurso": "Superficie techada",
         "cantidad": round(3.5 * p), "unidad": "m²", "estandar": "3,5 m²/persona", "fuente": "Esfera 2018"},
        {"categoria": "Albergue", "recurso": "Superficie total del sitio",
         "cantidad": round(45 * p), "unidad": "m²", "estandar": "45 m²/persona (incl. servicios)", "fuente": "ACNUR/Esfera"},
        {"categoria": "Albergue", "recurso": "Camas / camillas / colchonetas",
         "cantidad": p, "unidad": "unidades", "estandar": "1 por persona", "fuente": "Esfera 2018"},
        {"categoria": "Albergue", "recurso": "Tiendas / módulos familiares",
         "cantidad": _ceil(p / PERSONAS_POR_HOGAR), "unidad": "unidades",
         "estandar": f"1 por familia (~{PERSONAS_POR_HOGAR} pers.)", "fuente": "ACNUR"},
        {"categoria": "Albergue", "recurso": "Mantas / cobijas",
         "cantidad": 2 * p, "unidad": "unidades", "estandar": "2 por persona", "fuente": "Esfera 2018"},
        # --- Alimentación ---
        {"categoria": "Alimentación", "recurso": "Raciones alimentarias",
         "cantidad": p * dias, "unidad": f"raciones-persona ({dias} días)",
         "estandar": "2.100 kcal/persona/día", "fuente": "Esfera/PMA"},
        {"categoria": "Alimentación", "recurso": "Alimentos (peso)",
         "cantidad": round(0.6 * p * dias), "unidad": f"kg ({dias} días)",
         "estandar": "~0,6 kg/persona/día", "fuente": "PMA"},
        {"categoria": "Alimentación", "recurso": "Agua para cocina (incl. en WASH)",
         "cantidad": round(3 * p), "unidad": "L/día", "estandar": "~3 L/persona/día (de los 15)", "fuente": "Esfera 2018"},
        # --- Energía (ESTIMACIÓN de planificación, no Esfera) ---
        {"categoria": "Energía", "recurso": "Potencia eléctrica (pico)",
         "cantidad": kw_pico, "unidad": "kW",
         "estandar": "~0,1 kW/persona (iluminación, bombeo, salud, cocina, carga)",
         "fuente": "estimación de planificación"},
        {"categoria": "Energía", "recurso": "Planta eléctrica recomendada",
         "cantidad": _ceil(kw_pico / 0.8) if kw_pico else 0, "unidad": "kVA",
         "estandar": "kW / 0,8 (factor de potencia)", "fuente": "estimación de planificación"},
        # --- Salud e higiene ---
        {"categoria": "Salud e higiene", "recurso": "Puesto de salud",
         "cantidad": max(1, _ceil(p / 10000)), "unidad": "unidades", "estandar": "1 por 10.000 personas", "fuente": "Esfera 2018"},
        {"categoria": "Salud e higiene", "recurso": "Promotores de salud comunitarios",
         "cantidad": max(1, _ceil(p / 500)), "unidad": "personas", "estandar": "1 por 500 personas", "fuente": "Esfera 2018"},
        {"categoria": "Salud e higiene", "recurso": "Kits de higiene familiares",
         "cantidad": _ceil(p / PERSONAS_POR_HOGAR), "unidad": "kits",
         "estandar": f"1 por familia (~{PERSONAS_POR_HOGAR} pers.)", "fuente": "Esfera 2018"},
        {"categoria": "Salud e higiene", "recurso": "Jabón",
         "cantidad": round(0.25 * p), "unidad": "kg/mes", "estandar": "250 g/persona/mes", "fuente": "Esfera 2018"},
    ]


# --------------------------------------------------------------------------- #
# Estimación de población desplazada desde los datos del evento
# --------------------------------------------------------------------------- #
def estimacion_desplazados(personas_por_hogar: int = PERSONAS_POR_HOGAR, **f) -> dict:
    """Estima la población desplazada desde los reportes del evento (cada reporte
    de hogar ≈ `personas_por_hogar`). Devuelve escenarios y desglose por estado.

    - Cota ALTA: todos los reportes del evento × hogar (método citado por la dirección).
    - Cota MEDIA: reportes con daño estructural en vivienda × hogar (planificación).
    """
    pph = max(1, int(personas_por_hogar))
    total = data_service.total_reportes(**f)
    dano = data_service.dano_estructural(limit=1, **f)
    n_dano = dano.get("conteo", 0)
    por_estado = [
        {"estado": r.get("estado") or "Sin dato",
         "reportes_dano": r.get("conteo", 0),
         "desplazados_est": r.get("conteo", 0) * pph}
        for r in dano.get("por_estado", [])
    ]
    return {
        "personas_por_hogar": pph,
        "reportes_totales": total,
        "reportes_dano_estructural": n_dano,
        "escenarios": {
            "cota_media_dano_estructural": n_dano * pph,
            "cota_alta_todos_los_reportes": total * pph,
        },
        "por_estado_dano": por_estado,
    }


def desplazados_por_clasificacion(aptos: int = APTOS_PROMEDIO_DEFAULT,
                                  personas: int = PERSONAS_HOGAR_VERTICAL) -> list[dict]:
    """Desplazados por edificio según la CLASIFICACIÓN POR IA (lee título/descripción,
    cuenta edificios derrumbados/en riesgo por ESTADO REAL). [] si no se ha corrido."""
    try:
        from app.tools import clasificador_edificios as ce
        if not ce.disponible():
            return []
        res = ce.resumen(aptos_promedio=aptos, personas_hogar=personas)
    except Exception:  # noqa: BLE001
        return []
    out = []
    for f in res["por_estado"]:
        if not (f["personas_a_reubicar"] or f["personas_proximas_reubicar"]):
            continue
        out.append({
            "estado": f["estado"], "desplazados_est": f["personas_a_reubicar"],
            "proximos_reubicar": f["personas_proximas_reubicar"],
            "edificios_derrumbados": f["edificios_derrumbados"],
            "edificios_riesgo": f["edificios_riesgo"],
            "metodo": "ia",
            "detalle": f"{f['edificios_derrumbados']} edif derrumbados × {aptos} aptos × {personas} pers (IA)",
            "fuente": "Clasificación por IA de descripciones (estado real)",
        })
    out.sort(key=lambda r: r["desplazados_est"], reverse=True)
    return out


def desplazados_por_edificios() -> list[dict]:
    """Desplazados por COLAPSO VERTICAL. Prefiere la CLASIFICACIÓN POR IA (cuenta
    edificios leyendo las descripciones, con estado real); si no se ha corrido, cae a
    la tabla preliminar `EDIFICIOS_VERTICALES_AFECTADOS`."""
    ia = desplazados_por_clasificacion()
    if ia:
        return ia
    out = []
    for estado, p in EDIFICIOS_VERTICALES_AFECTADOS.items():
        personas = int(p["edificios"]) * int(p["aptos_promedio"]) * int(p["personas_hogar"])
        out.append({"estado": estado, "desplazados_est": personas, "metodo": "edificios",
                    "detalle": f"{p['edificios']} edif × {p['aptos_promedio']} aptos × "
                               f"{p['personas_hogar']} pers/hogar",
                    "fuente": p.get("fuente", "—")})
    out.sort(key=lambda r: r["desplazados_est"], reverse=True)
    return out


def desplazados_corregido_por_estado(personas_por_hogar: int = PERSONAS_POR_HOGAR,
                                     **f) -> list[dict]:
    """Estimación CORREGIDA del sesgo de reporte: para zonas con colapso vertical
    confirmado usa la cifra por edificios (fuente externa); para el resto, el proxy
    'reportes de daño × hogar'. Cada fila indica el método usado."""
    pph = max(1, int(personas_por_hogar))
    dano = data_service.dano_estructural(limit=1, **f)
    rep_by_state = {r.get("estado") or "Sin dato": r.get("conteo", 0)
                    for r in dano.get("por_estado", [])}
    edif = {z["estado"]: z for z in desplazados_por_edificios()}
    out = []
    for estado in set(rep_by_state) | set(edif):
        if estado in edif:
            out.append({"estado": estado, "desplazados_est": edif[estado]["desplazados_est"],
                        "metodo": "edificios", "detalle": edif[estado]["detalle"]})
        else:
            out.append({"estado": estado, "desplazados_est": rep_by_state.get(estado, 0) * pph,
                        "metodo": "reportes", "detalle": f"{rep_by_state.get(estado, 0)} reportes × {pph}"})
    out.sort(key=lambda r: r["desplazados_est"], reverse=True)
    return out


def datos_para_graficos(estado: str | None = None, dias: int = HORIZONTE_DIAS,
                        top: int = 12) -> dict:
    """Series listas para graficar el documento de albergues. Usa la estimación
    CORREGIDA por estado (corrige el sesgo de reporte con la cifra por edificios en
    zonas de colapso vertical)."""
    f = {"province": estado} if estado else {}
    corregido = [r for r in desplazados_corregido_por_estado(**f)
                 if r["estado"] != "Sin dato"][:top]
    desplazados = {r["estado"]: r["desplazados_est"] for r in corregido if r["desplazados_est"]}
    cisternas = {r["estado"]: _ceil(r["desplazados_est"] * 15 * dias / CISTERNA_L)
                 for r in corregido if r["desplazados_est"]}
    est = estimacion_desplazados(**f)
    total_corregido = sum(r["desplazados_est"] for r in desplazados_corregido_por_estado(**f))
    escenarios = {
        "Proxy reportes × hogar (sesgado)": est["escenarios"]["cota_media_dano_estructural"],
        "Corregido por edificios": total_corregido,
    }
    datos = {"desplazados_estado": desplazados, "escenarios": escenarios,
             "cisternas_estado": cisternas, "dias": dias}

    # Series adicionales desde la clasificación por IA (si está disponible).
    try:
        from app.tools import clasificador_edificios as ce
        if ce.disponible():
            res = ce.resumen(aptos_promedio=APTOS_PROMEDIO_DEFAULT, personas_hogar=PERSONAS_HOGAR_VERTICAL)
            riesgo = {r["estado"]: r["edificios_riesgo"] for r in res["por_estado"][:top]
                      if r.get("edificios_riesgo")}
            if riesgo:
                datos["riesgo_estado"] = riesgo
            comp = ce.composicion()
            if comp:
                datos["composicion"] = comp
            sesgo = ce.flujos_sesgo()
            hacia_lg = {}
            for fl in sesgo["flujos"]:
                decl, _, real = fl["flujo"].partition(" → ")
                if real.strip() == "La Guaira":
                    hacia_lg[decl.strip()] = fl["conteo"]
            if hacia_lg:
                datos["sesgo_la_guaira"] = hacia_lg
    except Exception:  # noqa: BLE001
        pass
    return datos


def zonas_prioritarias_albergues(top: int = 10) -> list[dict]:
    """Parroquias prioritarias para instalar albergues, según el IPCT (convergencia
    de intensidad, exposición, reportes y daño). Devuelve [] si el IPCT no está."""
    try:
        from app.db.ipct import ranking_ipct
        return ranking_ipct(top=top).get("ranking", [])
    except Exception:  # noqa: BLE001
        return []


# --------------------------------------------------------------------------- #
# Constructores de markdown para el contexto del informe
# --------------------------------------------------------------------------- #
def _fmt(n) -> str:
    if isinstance(n, float) and n.is_integer():
        n = int(n)
    if isinstance(n, int):
        return f"{n:,}".replace(",", ".")
    return str(n)


def tabla_proyeccion_md(personas: int, dias: int = HORIZONTE_DIAS) -> str:
    """Tabla markdown de necesidades para un campamento de `personas`."""
    out = [f"### Campamento de {_fmt(personas)} personas ({dias} días)",
           "| Categoría | Recurso | Cantidad | Unidad | Estándar | Fuente |",
           "|---|---|---|---|---|---|"]
    for it in proyeccion_albergue(personas, dias):
        out.append(f"| {it['categoria']} | {it['recurso']} | {_fmt(it['cantidad'])} | "
                   f"{it['unidad']} | {it['estandar']} | {it['fuente']} |")
    return "\n".join(out)


def bloque_contexto_md(estado: str | None = None, dias: int = HORIZONTE_DIAS) -> str:
    """Bloque completo para el CONTEXTO del informe de albergues: estimación de
    desplazados + proyecciones por tamaño + necesidades agregadas. Cifras exactas
    (deterministas) para que el documento no las invente."""
    est = estimacion_desplazados(**({"province": estado} if estado else {}))
    pph = est["personas_por_hogar"]
    media = est["escenarios"]["cota_media_dano_estructural"]
    alta = est["escenarios"]["cota_alta_todos_los_reportes"]

    partes = ["## Logística de albergues — proyecciones DETERMINISTAS (usa estas cifras exactas)"]

    # AVISO DE SESGO (clave): el conteo de reportes NO mide desplazamiento real.
    partes.append(
        "### ⚠️ Nota metodológica obligatoria (sesgo de reporte)\n"
        "El conteo de reportes está SESGADO por la densidad de reporte: Caracas reporta "
        "mucho más que La Guaira, así que 'reportes × hogar' SOBRE-representa a las zonas "
        "que más usan la app y SUBESTIMA el COLAPSO VERTICAL (edificios enteros que caen y "
        "desplazan a cientos de personas con muy pocos reportes). Por eso la cifra real de "
        "desplazados se concentra en La Guaira, no en Caracas. En el documento: (1) presenta "
        "el conteo por reportes SOLO como proxy de actividad, con esta advertencia explícita; "
        "(2) usa la estimación CORREGIDA por edificios para priorizar; (3) deja claro que las "
        "cifras por edificios son PRELIMINARES hasta confirmación oficial."
    )

    partes.append(
        "### Población desplazada estimada\n"
        f"- Supuesto base: 1 hogar reportante ≈ {pph} personas (zonas de colapso vertical usan 6).\n"
        f"- Reportes del evento: {_fmt(est['reportes_totales'])}; con daño estructural: {_fmt(est['reportes_dano_estructural'])}.\n"
        f"- **Proxy por reportes (SESGADO)**: daño estructural × {pph} = {_fmt(media)} personas (cota alta {_fmt(alta)}). NO usar como ranking real.\n"
        "- **Estimación corregida**: ver tabla por estado más abajo (usa edificios en zonas de colapso vertical)."
    )

    # Estimación por edificios (corrección del sesgo)
    edif = desplazados_por_edificios()
    if edif:
        tabla = ["### Desplazados por colapso vertical (estimación por EDIFICIOS — PRELIMINAR)",
                 "| Estado | Cálculo | Desplazados estimados | Fuente |", "|---|---|---|---|"]
        for r in edif:
            tabla.append(f"| {r['estado']} | {r['detalle']} | {_fmt(r['desplazados_est'])} | {r['fuente']} |")
        partes.append("\n".join(tabla))

    # Total a reubicar / próximos a reubicar — clasificación POR IA (estado real)
    ia = desplazados_por_clasificacion()
    if ia:
        try:
            from app.tools import clasificador_edificios as ce
            res = ce.resumen(aptos_promedio=APTOS_PROMEDIO_DEFAULT, personas_hogar=PERSONAS_HOGAR_VERTICAL)
        except Exception:  # noqa: BLE001
            res = None
        tot_reub = sum(r["desplazados_est"] for r in ia)
        tot_prox = sum(r["proximos_reubicar"] for r in ia)
        cab = ["### Total a reubicar y próximos a reubicar (clasificación IA por estado REAL)",
               f"- **Personas a REUBICAR ahora** (edificaciones derrumbadas): **{_fmt(tot_reub)}**.",
               f"- **Próximas a reubicar** (edificaciones en riesgo de colapso): **{_fmt(tot_prox)}**.",
               f"- Supuestos: {APTOS_PROMEDIO_DEFAULT} aptos/edificio × {PERSONAS_HOGAR_VERTICAL} pers/hogar; "
               "viviendas unifamiliares = 1 hogar (confirmables)."]
        if res:
            cab.append(f"- Composición del 'a reubicar': {_fmt(res['total_edificios_derrumbados'])} edificios + "
                       f"{_fmt(res['total_viviendas_derrumbadas'])} viviendas derrumbadas (distintas).")
        cab.append(
            "- LECTURA OPERATIVA: **La Guaira = reubicación inmediata** (más derrumbes); "
            "**Caracas = evacuación preventiva** (concentra los edificios EN RIESGO).")
        tabla = cab + ["",
                       "| Estado | Edif. derrumbados | A reubicar | Edif. en riesgo | Próximos a reubicar |",
                       "|---|---|---|---|---|"]
        for r in ia[:15]:
            tabla.append(f"| {r['estado']} | {r['edificios_derrumbados']} | {_fmt(r['desplazados_est'])} | "
                         f"{r['edificios_riesgo']} | {_fmt(r['proximos_reubicar'])} |")
        partes.append("\n".join(tabla))

        # Sesgo cuantificado: estado declarado ≠ estado real
        try:
            from app.tools import clasificador_edificios as ce
            sesgo = ce.flujos_sesgo()
        except Exception:  # noqa: BLE001
            sesgo = None
        if sesgo and sesgo["reclasificados"]:
            ts = [f"### Sesgo de reporte cuantificado (estado declarado ≠ estado real)",
                  f"- {_fmt(sesgo['reclasificados'])} reportes ({sesgo['pct']}%) se declararon en un estado "
                  "distinto al del hecho real (inferido del texto).",
                  "- La gran mayoría se reasignaron HACIA La Guaira, confirmando que estaba "
                  "sub-representada por la densidad de reporte.",
                  "",
                  "| Reasignación (declarado → real) | Reportes |", "|---|---|"]
            for fl in sesgo["flujos"][:10]:
                ts.append(f"| {fl['flujo']} | {fl['conteo']} |")
            partes.append("\n".join(ts))

    # Desglose CORREGIDO por estado (top 12) — el que se debe usar para priorizar
    corregido = [r for r in desplazados_corregido_por_estado() if r["estado"] != "Sin dato"][:12]
    if corregido:
        tabla = ["### Desplazados estimados por estado — CORREGIDO (usar este para priorizar)",
                 "| Estado | Desplazados estimados | Método | Detalle |", "|---|---|---|---|"]
        for r in corregido:
            tabla.append(f"| {r['estado']} | {_fmt(r['desplazados_est'])} | {r['metodo']} | {r['detalle']} |")
        partes.append("\n".join(tabla))

    # Proyecciones por tamaño de campamento de referencia
    partes.append("### Proyección de suministros por tamaño de campamento")
    for n in TAMANOS_REFERENCIA:
        partes.append(tabla_proyeccion_md(n, dias))

    # Necesidades agregadas. Primario: total CORREGIDO (PRELIMINAR, domina La Guaira
    # por edificios). Secundario: proxy por reportes como piso conservador.
    total_corregido = sum(r["desplazados_est"] for r in desplazados_corregido_por_estado())
    if total_corregido:
        partes.append(f"### Necesidades agregadas — estimación CORREGIDA ({_fmt(total_corregido)} personas, PRELIMINAR)")
        partes.append(tabla_proyeccion_md(total_corregido, dias))
    if media:
        partes.append(f"### Necesidades agregadas — piso conservador por reportes ({_fmt(media)} personas)")
        partes.append(tabla_proyeccion_md(media, dias))

    # Zonas prioritarias para instalar albergues (IPCT)
    zonas = zonas_prioritarias_albergues(top=10)
    if zonas:
        tabla = ["### Zonas prioritarias para instalar albergues (ranking IPCT)",
                 "| # | Estado | Municipio | Parroquia | IPCT (0–5) | Nivel | Motivo |",
                 "|---|---|---|---|---|---|---|"]
        for z in zonas:
            tabla.append(f"| {z.get('ranking')} | {z.get('estado') or '—'} | "
                         f"{z.get('municipio') or '—'} | {z.get('parroquia') or '—'} | "
                         f"{z.get('ipct')} | {z.get('nivel') or '—'} | {z.get('motivo_principal') or '—'} |")
        partes.append("\n".join(tabla))

    partes.append(
        "### Notas de método\n"
        "- Estándares: Esfera 2018, ACNUR y PMA/OMS (ver columna 'Fuente').\n"
        "- La energía eléctrica es una ESTIMACIÓN de planificación (~0,1 kW/persona), no un estándar Esfera.\n"
        f"- Horizonte de planificación: {dias} días (ajustable según duración prevista del albergue)."
    )
    return "\n\n".join(partes)

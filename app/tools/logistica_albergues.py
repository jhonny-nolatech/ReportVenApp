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


def datos_para_graficos(estado: str | None = None, dias: int = HORIZONTE_DIAS,
                        top: int = 12) -> dict:
    """Series listas para graficar el documento de albergues:
    - desplazados estimados por estado,
    - escenarios (cota media vs. cota alta),
    - camiones cisterna requeridos por estado en el horizonte.
    """
    est = estimacion_desplazados(**({"province": estado} if estado else {}))
    filas = [r for r in est["por_estado_dano"] if r["estado"] != "Sin dato"][:top]
    desplazados = {r["estado"]: r["desplazados_est"] for r in filas if r["desplazados_est"]}
    cisternas = {r["estado"]: _ceil(r["desplazados_est"] * 15 * dias / CISTERNA_L)
                 for r in filas if r["desplazados_est"]}
    escenarios = {
        "Cota media (planificación)": est["escenarios"]["cota_media_dano_estructural"],
        "Cota alta (máx. demanda)": est["escenarios"]["cota_alta_todos_los_reportes"],
    }
    return {"desplazados_estado": desplazados, "escenarios": escenarios,
            "cisternas_estado": cisternas, "dias": dias}


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
    partes.append(
        "### Población desplazada estimada\n"
        f"- Supuesto: 1 hogar reportante ≈ {pph} personas.\n"
        f"- Reportes del evento: {_fmt(est['reportes_totales'])}; con daño estructural: {_fmt(est['reportes_dano_estructural'])}.\n"
        f"- **Cota media (planificación)**: daño estructural × {pph} = **{_fmt(media)} personas**.\n"
        f"- **Cota alta**: todos los reportes × {pph} = **{_fmt(alta)} personas**.\n"
        "- Usa la cota media para planificar y menciona la cota alta como escenario de máxima demanda."
    )
    # Desglose por estado (top 12)
    filas = est["por_estado_dano"][:12]
    if filas:
        tabla = ["### Desplazados estimados por estado (daño estructural × hogar)",
                 "| Estado | Reportes con daño | Desplazados estimados |", "|---|---|---|"]
        for r in filas:
            tabla.append(f"| {r['estado']} | {_fmt(r['reportes_dano'])} | {_fmt(r['desplazados_est'])} |")
        partes.append("\n".join(tabla))

    # Proyecciones por tamaño de campamento de referencia
    partes.append("### Proyección de suministros por tamaño de campamento")
    for n in TAMANOS_REFERENCIA:
        partes.append(tabla_proyeccion_md(n, dias))

    # Necesidades agregadas para la cota media
    if media:
        partes.append("### Necesidades agregadas para la cota media de planificación")
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

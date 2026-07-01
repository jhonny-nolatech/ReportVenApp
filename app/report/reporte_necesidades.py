"""Termómetro de Necesidades Emergentes (.docx) — Terremoto 24J.

Eje TEMPORAL/PREDICTIVO: ¿qué necesidad está CRECIENDO y qué hay que pre-posicionar
ANTES de que explote? Clasifica cada reporte por tipo de necesidad (rescate, vivienda,
agua, electricidad, salud, alimentación) por palabras clave y sigue su evolución día a
día. La señal clave es el CAMBIO DE COMPOSICIÓN (share): el volumen total cae con los
días, pero la PROPORCIÓN de ciertas necesidades sube (p. ej. rescate/personas conforme
se cierra la ventana; salud y agua en la fase de recuperación).

Determinista (no usa IA / no consume tokens). Salida .docx en reports_out/.
"""
from __future__ import annotations

import os
import re

from app.config import Settings
from app.db.mongo import build_event_query, get_reports_collection
from app.report.charts import grafico_lineas_multiple
from app.report.markdown_docx import render_markdown

# Categorías de necesidad (una necesidad puede caer en varias — refleja la realidad).
_CATS = {
    "Rescate y personas": r"atrapad|bajo (los )?escombros|sepultad|rescat|desaparec|herid|no aparece|cad[aá]ver|fallecid",
    "Vivienda y albergue": r"vivienda|\bcasa\b|edificio|techo|refugio|albergue|damnificad|sin hogar|desplazad",
    "Agua y saneamiento": r"\bagua|tuber[ií]a|acueducto|cloaca|aguas (negras|servidas)|potable",
    "Electricidad": r"electric|\bluz\b|corriente|apag[oó]n|poste|cable|transformador|sin luz",
    "Salud": r"hospital|cl[ií]nica|medicina|medicament|enferm|\bsalud\b|ambulanci",
    "Alimentación": r"comida|aliment|hambr|mercado|v[íi]veres|desabastec",
}
_CATS_RX = {k: re.compile(v, re.I) for k, v in _CATS.items()}


def series_necesidades() -> dict:
    """Series diarias por categoría (absoluto y % del día) + tendencia reciente."""
    col = get_reports_collection()
    por_dia: dict[str, dict[str, int]] = {}
    tot_dia: dict[str, int] = {}
    for d in col.find(build_event_query()):
        ts = d.get("createdAt")
        if not ts:
            continue
        dia = ts.strftime("%Y-%m-%d")
        tot_dia[dia] = tot_dia.get(dia, 0) + 1
        cd = por_dia.setdefault(dia, {c: 0 for c in _CATS})
        txt = f"{d.get('title') or ''} {d.get('description') or ''}"
        for c, rx in _CATS_RX.items():
            if rx.search(txt):
                cd[c] += 1
    periodos = sorted(tot_dia)
    absoluto = {c: [por_dia.get(p, {}).get(c, 0) for p in periodos] for c in _CATS}
    share = {c: [round(100 * por_dia.get(p, {}).get(c, 0) / (tot_dia[p] or 1), 1) for p in periodos]
             for c in _CATS}

    # Tendencia: share reciente (últimos 2 días) vs inicial (días 2–3, se salta el 1º).
    trend = {}
    for c in _CATS:
        s = share[c]
        recientes = s[-2:] if len(s) >= 2 else s
        iniciales = s[1:3] if len(s) >= 3 else s[:2]
        pr = sum(recientes) / len(recientes) if recientes else 0
        pi = sum(iniciales) / len(iniciales) if iniciales else 0
        delta = pr - pi
        flecha = "▲ subiendo" if delta > 1.5 else "▼ bajando" if delta < -1.5 else "▶ estable"
        trend[c] = {"share_ini": round(pi, 1), "share_rec": round(pr, 1),
                    "delta": round(delta, 1), "tendencia": flecha,
                    "total": sum(absoluto[c])}
    return {"periodos": periodos, "absoluto": absoluto, "share": share, "trend": trend}


def _fmt(n) -> str:
    try:
        return f"{int(round(n)):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(n)


def generar_reporte(out_path: str | None = None) -> str:
    s = series_necesidades()
    outdir = Settings().reports_out_dir
    out_path = out_path or os.path.join(outdir, "Termometro de necesidades emergentes - Terremoto 24J.docx")

    periodos, share, trend = s["periodos"], s["share"], s["trend"]
    emergentes = sorted([c for c in _CATS if trend[c]["delta"] > 1.5],
                        key=lambda c: trend[c]["delta"], reverse=True)
    bajando = [c for c in _CATS if trend[c]["delta"] < -1.5]

    # Gráfica: evolución de la COMPOSICIÓN (share %) por categoría.
    img = ""
    if len(periodos) >= 2:
        ruta = grafico_lineas_multiple(
            periodos, share,
            "Composición de las necesidades en el tiempo (% de reportes por día)",
            os.path.join(outdir, "charts", "necesidades.png"),
            fuente="Fuente: reportes VenApp clasificados por necesidad · % del total del día.")
        img = f"![Composición de necesidades en el tiempo]({ruta})"

    def _linea(cs):
        return ", ".join(f"**{c}** ({trend[c]['share_ini']}%→{trend[c]['share_rec']}%)" for c in cs) or "—"

    tabla = ["## Termómetro por categoría de necesidad",
             "| Necesidad | Reportes (total) | % inicial | % reciente | Tendencia |",
             "|---|---|---|---|---|"]
    for c in sorted(_CATS, key=lambda x: trend[x]["delta"], reverse=True):
        t = trend[c]
        tabla.append(f"| {c} | {_fmt(t['total'])} | {t['share_ini']}% | {t['share_rec']}% | {t['tendencia']} |")

    partes = [
        "# Termómetro de necesidades emergentes — Terremoto 24J",
        "## Resumen ejecutivo",
        "El volumen de reportes baja con los días, pero la **composición de las necesidades cambia**: "
        "es lo que hay que anticipar. Necesidades **EN ASCENSO** (pre-posicionar recursos ya): "
        f"{_linea(emergentes)}. Necesidades que **ceden**: {_linea(bajando)}.",
        "## Cómo evolucionan las necesidades",
    ]
    if img:
        partes.append(img)
    partes += [
        "\n".join(tabla),
        "## Lectura operativa",
        "- **% reciente > % inicial (▲)** = necesidad emergente: su peso relativo crece, hay que "
        "reforzarla aunque el total de reportes baje.\n"
        "- El patrón típico post-terremoto: **rescate/personas** gana peso mientras se cierra la "
        "ventana de vida; **electricidad** cede al restablecerse; **agua, salud y albergue** dominan "
        "la fase de recuperación. Úsalo para pasar de reaccionar a **anticipar**.",
        "## Acción recomendada",
        "1. Pre-posicionar recursos de las categorías **en ascenso** en las próximas 48–72 h.\n"
        "2. Reorientar capacidad desde las categorías que ceden hacia las que crecen.\n"
        "3. Revisar este termómetro en cada corte (09:00 / 18:00) para detectar giros temprano.",
        "## Método",
        "Cada reporte se asigna a una o más categorías por palabras clave en título y descripción. "
        "La tendencia compara el % de reportes de cada categoría en los últimos 2 días vs. los primeros "
        "días. Es una señal de priorización, no un pronóstico de casos.",
    ]
    return render_markdown("\n\n".join(partes), out_path)

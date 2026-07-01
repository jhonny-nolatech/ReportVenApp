"""Reporte de Zonas Silenciosas / Puntos Ciegos (.docx) — Terremoto 24J.

Producto de decisión para el comité de crisis: ¿DÓNDE hay probable daño del que NO
nos estamos enterando? Cruza intensidad sísmica (MMI) × población × reportes
recibidos para detectar localidades de alta exposición con baja/nula recepción de
reportes — probables zonas con comunicaciones caídas o acceso cortado.

REGLA RECTORA: baja recepción de reportes NO significa ausencia de daño; es una
ZONA DE ATENCIÓN que debe priorizarse para verificación en terreno.

Determinista (no usa IA / no consume tokens). Salida .docx en reports_out/.
"""
from __future__ import annotations

import os

from app.config import Settings
from app.db.zonas_silenciosas import analizar_puntos_ciegos
from app.report.charts import grafico_barras, ROJO
from app.report.markdown_docx import render_markdown


def _fmt(n) -> str:
    try:
        return f"{int(round(n)):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(n)


def _tabla(zonas, titulo: str) -> str:
    out = [f"## {titulo}",
           "| # | Localidad | Estado | MMI | Habitantes | Reportes recibidos | Esperados | Cobertura |",
           "|---|---|---|---|---|---|---|---|"]
    for i, z in enumerate(zonas, 1):
        out.append(f"| {i} | {z.localidad} | {z.estado or '—'} | {z.mmi} | {_fmt(z.habitantes)} | "
                   f"{_fmt(z.reportes_observados)} | {_fmt(z.reportes_esperados)} | {z.cobertura:.0%} |")
    return "\n".join(out)


def generar_reporte(out_path: str | None = None, top: int = 12) -> str:
    """Genera el .docx de zonas silenciosas. Devuelve la ruta."""
    a = analizar_puntos_ciegos()
    s = Settings()
    outdir = s.reports_out_dir
    out_path = out_path or os.path.join(outdir, "Zonas silenciosas y puntos ciegos - Terremoto 24J.docx")

    criticas = a.zonas_criticas[:top]
    silenciosas = a.zonas_silenciosas[:top]

    # Gráfica: reportes FALTANTES (esperados - observados) en las zonas de atención.
    zonas_graf = (a.zonas_criticas + a.zonas_silenciosas)
    deficit = {z.localidad: max(0, round(z.reportes_esperados - z.reportes_observados))
               for z in zonas_graf}
    deficit = dict(sorted(deficit.items(), key=lambda x: x[1], reverse=True)[:12])
    img = ""
    if deficit:
        ruta = grafico_barras(
            deficit, "Reportes faltantes en zonas de atención (esperados − recibidos)",
            os.path.join(outdir, "charts", "zonas_silenciosas.png"), color=ROJO,
            fuente="Fuente: cruce MMI × población × reportes VenApp · corte del análisis.")
        img = f"![Reportes faltantes por zona]({ruta})"

    top_nombres = ", ".join(z.localidad for z in criticas[:5]) or "—"
    partes = [
        "# Zonas silenciosas y puntos ciegos — Terremoto 24J",
        "## Resumen ejecutivo",
        f"Se detectaron **{len(a.zonas_criticas)} zonas críticas** y **{len(a.zonas_silenciosas)} "
        "silenciosas**: localidades con alta intensidad sísmica y mucha población pero **muy pocos "
        "reportes**. La baja recepción **NO significa que no haya daño** — lo más probable es que "
        "tengan las comunicaciones o el acceso cortados. **Son la prioridad #1 para enviar equipos "
        f"de reconocimiento.** Verificación inmediata sugerida: **{top_nombres}**.",
    ]
    if img:
        partes += ["## Reportes faltantes (dónde están los vacíos de información)", img]
    partes += [
        _tabla(criticas, "Zonas críticas — verificación en terreno INMEDIATA"),
        _tabla(silenciosas, "Zonas silenciosas — vigilar y confirmar"),
        "## Cómo leer esto",
        "- **Cobertura** = reportes recibidos ÷ reportes esperados (según intensidad y población). "
        "Cobertura baja = probable subregistro, no ausencia de daño.\n"
        "- **Esperados** se estima con la tasa de reporte de las zonas que sí reportan, escalada por "
        "exposición (MMI × población). Es una heurística de priorización, no un conteo de víctimas.\n"
        "- Regla rectora: toda zona de baja cobertura se trata como **ZONA DE ATENCIÓN**.",
        "## Acción recomendada",
        f"1. Desplegar reconocimiento/telecom a las {min(5, len(criticas))} zonas críticas del tope.\n"
        "2. Restablecer comunicaciones (satelital/móvil) donde la cobertura sea más baja.\n"
        "3. Confirmar estado y reabrir el canal de reportes; re-priorizar con el próximo corte.",
    ]
    md = "\n\n".join(partes)
    return render_markdown(md, out_path)

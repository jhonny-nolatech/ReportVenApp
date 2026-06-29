"""Generación de gráficos para los informes (matplotlib, backend headless).

Convierte cifras agregadas en gráficos de torta/barras con estética
institucional, pensados para visualizar dónde concentrar recursos en vez de
presentar solo "números cerrados". Render determinista (sin IA).

Uso típico:
    from app.report.charts import graficos_infraestructura
    rutas = graficos_infraestructura(stats, outdir="reports_out")
    # rutas = {"servicios": ".../infra_servicios.png", ...}
"""
from __future__ import annotations
import os
import matplotlib
matplotlib.use("Agg")  # sin display
import matplotlib.pyplot as plt

# Paleta institucional + semáforo
AZUL = "#0B3C5D"
AZUL2 = "#1D6FA3"
ROJO = "#C0392B"
NARANJA = "#E67E22"
VERDE = "#27AE60"
GRIS = "#95A5A6"
AMARILLO = "#F1C40F"
TEAL = "#16A085"
PALETA = [AZUL2, ROJO, NARANJA, VERDE, TEAL, AMARILLO, GRIS, AZUL]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
})


def _autopct(total: int):
    def fmt(pct):
        n = int(round(pct * total / 100.0))
        return f"{pct:.0f}%\n({n:,})".replace(",", ".")
    return fmt


def grafico_torta(datos: dict, titulo: str, ruta: str,
                  subtitulo: str | None = None, colores: list | None = None,
                  fuente: str | None = None) -> str:
    """Genera una torta (dona) a partir de {etiqueta: valor}. Devuelve la ruta."""
    datos = {k: v for k, v in datos.items() if v and v > 0}
    labels = list(datos.keys())
    valores = list(datos.values())
    total = sum(valores)
    colores = (colores or PALETA)[:len(valores)]

    fig, ax = plt.subplots(figsize=(6.2, 4.6), dpi=150)
    wedges, _texts, autotexts = ax.pie(
        valores, colors=colores, startangle=90, counterclock=False,
        autopct=_autopct(total), pctdistance=0.74,
        wedgeprops=dict(width=0.42, edgecolor="white", linewidth=1.5),
    )
    for at in autotexts:
        at.set_color("white"); at.set_fontsize(9); at.set_fontweight("bold")
    ax.set_title(titulo, color=AZUL, pad=14)
    if subtitulo:
        ax.text(0.5, 1.005, subtitulo, transform=ax.transAxes,
                ha="center", va="bottom", fontsize=9.5, color=GRIS)
    ax.text(0, 0, f"{total:,}".replace(",", "."), ha="center", va="center",
            fontsize=18, fontweight="bold", color=AZUL)
    ax.legend(wedges, [f"{l}  ({v:,})".replace(",", ".") for l, v in zip(labels, valores)],
              loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False, fontsize=9.5)
    if fuente:
        fig.text(0.01, 0.01, fuente, fontsize=7.5, color=GRIS, ha="left")
    ax.set(aspect="equal")
    fig.tight_layout()
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    fig.savefig(ruta, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return ruta


def grafico_barras(datos: dict, titulo: str, ruta: str,
                   color: str = AZUL2, fuente: str | None = None) -> str:
    """Barras horizontales {etiqueta: valor}, ordenadas de mayor a menor."""
    items = sorted(((k, v) for k, v in datos.items() if v is not None),
                   key=lambda x: x[1], reverse=True)
    labels = [k for k, _ in items]
    valores = [v for _, v in items]
    fig, ax = plt.subplots(figsize=(6.6, 0.55 * len(items) + 1.4), dpi=150)
    bars = ax.barh(labels, valores, color=color, edgecolor="white")
    ax.invert_yaxis()
    for b, v in zip(bars, valores):
        ax.text(b.get_width() + max(valores) * 0.01, b.get_y() + b.get_height() / 2,
                f"{v:,}".replace(",", "."), va="center", fontsize=9.5, color=AZUL, fontweight="bold")
    ax.set_title(titulo, color=AZUL, pad=12)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlim(0, max(valores) * 1.15)
    if fuente:
        fig.text(0.01, 0.01, fuente, fontsize=7.5, color=GRIS, ha="left")
    fig.tight_layout()
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    fig.savefig(ruta, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return ruta


def grafico_linea(datos, titulo: str, ruta: str, color: str = AZUL2,
                  fuente: str | None = None) -> str:
    """Serie temporal {etiqueta: valor} (o lista de pares) como línea con área."""
    items = list(datos.items()) if isinstance(datos, dict) else list(datos)
    labels = [k for k, _ in items]
    valores = [v for _, v in items]
    xs = list(range(len(labels)))
    fig, ax = plt.subplots(figsize=(7.4, 4.0), dpi=150)
    ax.plot(xs, valores, marker="o", color=color, linewidth=2, markersize=5)
    ax.fill_between(xs, valores, color=color, alpha=0.12)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8.5)
    for x, v in zip(xs, valores):
        ax.text(x, v + (max(valores) or 1) * 0.025, f"{v:,}".replace(",", "."),
                ha="center", fontsize=8, color=AZUL, fontweight="bold")
    ax.set_title(titulo, color=AZUL, pad=12)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_ylim(0, (max(valores) or 1) * 1.2)
    if fuente:
        fig.text(0.01, 0.01, fuente, fontsize=7.5, color=GRIS, ha="left")
    fig.tight_layout()
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    fig.savefig(ruta, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return ruta


def grafico_lineas_multiple(periodos, series: dict, titulo: str, ruta: str,
                            colores: list | None = None, fuente: str | None = None) -> str:
    """Varias series temporales sobre los mismos `periodos`. `series` = {nombre: [v...]}."""
    xs = list(range(len(periodos)))
    colores = colores or [AZUL, ROJO, NARANJA, TEAL, VERDE, AMARILLO, GRIS]
    fig, ax = plt.subplots(figsize=(7.8, 4.4), dpi=150)
    for i, (nombre, valores) in enumerate(series.items()):
        ax.plot(xs, valores, marker="o", markersize=4, linewidth=2,
                color=colores[i % len(colores)], label=nombre)
    ax.set_xticks(xs)
    ax.set_xticklabels(periodos, rotation=45, ha="right", fontsize=8.5)
    ax.set_title(titulo, color=AZUL, pad=12)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    maxv = max((max(v) for v in series.values() if v), default=1)
    ax.set_ylim(0, (maxv or 1) * 1.2)
    if fuente:
        fig.text(0.01, 0.01, fuente, fontsize=7.5, color=GRIS, ha="left")
    fig.tight_layout()
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    fig.savefig(ruta, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return ruta


def graficos_panorama(panorama: dict, outdir: str = "reports_out",
                      fuente: str | None = None) -> dict:
    """Gráficos DETERMINISTAS a partir del `panorama_completo` de data_service
    (no dependen de la prosa del LLM, así que siempre se generan si hay datos):
      - Reportes por tipo de emergencia (subcategoría).
      - Estados más afectados por volumen de reportes.
      - Evolución diaria de reportes ciudadanos.
    Devuelve {nombre: ruta_png}.
    """
    rutas: dict = {}
    fuente = fuente or "Fuente: reportes ciudadanos VenApp · corte del análisis."
    panorama = panorama or {}

    sub = {r.get("subcategoria"): r.get("conteo") for r in (panorama.get("por_subcategoria") or [])
           if r.get("subcategoria") and r.get("subcategoria") != "Sin dato"}
    if sub:
        rutas["tipo_emergencia"] = grafico_barras(
            dict(list(sub.items())[:10]), "Reportes por tipo de emergencia",
            os.path.join(outdir, "pan_tipo_emergencia.png"), color=AZUL2, fuente=fuente)

    est = {r.get("estado"): r.get("conteo") for r in (panorama.get("por_estado_geografico") or [])
           if r.get("estado") and r.get("estado") != "Sin dato"}
    if est:
        rutas["estados"] = grafico_barras(
            dict(list(est.items())[:10]), "Estados más afectados (volumen de reportes)",
            os.path.join(outdir, "pan_estados.png"), color=ROJO, fuente=fuente)

    # Evolución diaria desde el 24J: total + desglose por tipo (edificaciones,
    # personas, servicios). Si no hay desglose, cae a una sola línea de total.
    evo_tipo = panorama.get("evolucion_por_tipo") or {}
    periodos = evo_tipo.get("periodos") or [r.get("periodo") for r in (panorama.get("evolucion_temporal") or [])]
    series = {k: v for k, v in (evo_tipo.get("series") or {}).items() if any(v)}
    if periodos and len(periodos) >= 2 and series:
        rutas["evolucion"] = grafico_lineas_multiple(
            periodos, series, "Evolución diaria desde el 24J (reportes y afectaciones)",
            os.path.join(outdir, "pan_evolucion.png"), fuente=fuente)
    elif len(periodos) >= 2:
        evo = [(r.get("periodo"), r.get("conteo")) for r in (panorama.get("evolucion_temporal") or [])
               if r.get("periodo")]
        rutas["evolucion"] = grafico_linea(
            evo, "Evolución diaria de reportes ciudadanos",
            os.path.join(outdir, "pan_evolucion.png"), fuente=fuente)

    return rutas


def graficos_albergues(datos: dict, outdir: str = "reports_out",
                       fuente: str | None = None) -> dict:
    """Gráficos del documento de albergues/desplazados, a partir de las series de
    `logistica_albergues.datos_para_graficos`: desplazados por estado, escenarios
    de demanda y camiones cisterna por estado. Devuelve {nombre: ruta_png}."""
    rutas: dict = {}
    datos = datos or {}
    fuente = fuente or "Fuente: estimación VenApp (reportes × hogar) · estándares Esfera/ACNUR/PMA."
    dias = datos.get("dias", 14)

    if datos.get("desplazados_estado"):
        rutas["desplazados_estado"] = grafico_barras(
            datos["desplazados_estado"], "Desplazados estimados por estado",
            os.path.join(outdir, "alb_desplazados_estado.png"), color=ROJO, fuente=fuente)
    if datos.get("escenarios"):
        rutas["escenarios"] = grafico_barras(
            datos["escenarios"], "Escenarios de población desplazada",
            os.path.join(outdir, "alb_escenarios.png"), color=AZUL2, fuente=fuente)
    if datos.get("cisternas_estado"):
        rutas["cisternas_estado"] = grafico_barras(
            datos["cisternas_estado"],
            f"Camiones cisterna (10.000 L) en {dias} días por estado",
            os.path.join(outdir, "alb_cisternas.png"), color=TEAL, fuente=fuente)
    return rutas


def graficos_infraestructura(stats: dict, outdir: str = "reports_out",
                             fuente: str | None = None) -> dict:
    """Construye los gráficos estándar de la sección de infraestructura.

    `stats` admite las claves (todas opcionales):
      electricidad: {"Cortes de energía":398, "Cables expuestos":180, ...}
      gas:          {"Fugas de gas":90, "Incendios":14}
      agua:         {"Roturas de tuberías":58}
      telecom:      {"Interrupciones":37}
      salud:        {"Red activada (públicos+clínicas)":19, "Hosp. de campaña":3,
                     "Con daño estructural / no operativos":8}
    Devuelve {nombre: ruta_png}.
    """
    rutas = {}
    fuente = fuente or "Fuente: agregados VenApp · corte del análisis."

    # 1) Distribución de incidencias por sector (resource allocation)
    sector = {}
    if stats.get("electricidad"): sector["Electricidad"] = sum(stats["electricidad"].values())
    if stats.get("gas"): sector["Gas"] = sum(stats["gas"].values())
    if stats.get("agua"): sector["Agua"] = sum(stats["agua"].values())
    if stats.get("telecom"): sector["Telecomunicaciones"] = sum(stats["telecom"].values())
    if sector:
        rutas["servicios"] = grafico_torta(
            sector, "Incidencias en servicios por sector",
            os.path.join(outdir, "infra_servicios.png"),
            subtitulo="Dónde concentrar cuadrillas de respuesta",
            colores=[AMARILLO, ROJO, AZUL2, TEAL], fuente=fuente)

    # 2) Daño eléctrico por tipo
    if stats.get("electricidad"):
        rutas["electricidad"] = grafico_torta(
            stats["electricidad"], "Daño eléctrico por tipo",
            os.path.join(outdir, "infra_electricidad.png"),
            subtitulo="Define materiales y especialidad de cuadrilla",
            fuente=fuente)

    # 3) Estado de la red hospitalaria
    if stats.get("salud"):
        rutas["salud"] = grafico_torta(
            stats["salud"], "Reportes en salud, escuelas y edificios públicos",
            os.path.join(outdir, "infra_salud.png"),
            colores=[ROJO, AZUL2, GRIS], fuente=fuente)

    return rutas

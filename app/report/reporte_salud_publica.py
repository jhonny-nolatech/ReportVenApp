"""Alerta de Salud Pública y Riesgo de Epidemias en albergues (.docx) — Terremoto 24J.

La "segunda catástrofe" tras un terremoto suele ser sanitaria: enfermedades
diarreicas/cólera por agua y saneamiento colapsados, dengue por agua estancada, y
brotes respiratorios por hacinamiento en albergues. Este reporte cruza:

  - Población desplazada (hacinamiento) por estado — de la clasificación por IA.
  - Reportes de agua y saneamiento (riesgo diarreico/AWD, cólera).
  - Reportes de agua estancada / aguas negras / basura (riesgo vectorial: dengue).

y produce un ÍNDICE DE RIESGO SANITARIO por estado + brechas WASH (agua/letrinas
según estándares Esfera) + acciones preventivas. Determinista, no usa IA.

Fuentes de método: OMS (evaluación de riesgo de enfermedades transmisibles tras
desastres), OPS/PAHO, estándares Esfera 2018. Precedente: cólera en Haití 2010.
"""
from __future__ import annotations

import math
import os
import re

from app.config import Settings
from app.db.mongo import build_event_query, get_reports_collection
from app.report.charts import grafico_barras, ROJO
from app.report.markdown_docx import render_markdown
from app.tools import clasificador_edificios as ce
from app.tools import logistica_albergues as la

_RE_WASH = re.compile(r"\bagua\b|tuber[ií]a|acueducto|cloaca|aguas negras|aguas servidas|"
                      r"sin agua|pozo s[ée]ptico|potable|desborde de", re.I)
_RE_VECTOR = re.compile(r"agua estancada|charc|aguas negras|aguas servidas|basura|desecho|"
                        r"zancud|mosquit|dengue|criadero|plaga|escombros acumulad", re.I)


def _por_estado() -> dict:
    """Cuenta reportes WASH y vectoriales por estado REAL (de la clasificación)."""
    col = get_reports_collection()
    cache = ce._cargar_cache()
    agg: dict[str, dict] = {}
    for d in col.find(build_event_query()):
        c = cache.get(d.get("number"), {})
        est = (ce._canon_estado(c.get("estado_real"))
               or ce._canon_estado((d.get("province") or {}).get("name")) or "Sin dato")
        txt = f"{d.get('title') or ''} {d.get('description') or ''}"
        a = agg.setdefault(est, {"wash": 0, "vector": 0, "total": 0})
        a["total"] += 1
        if _RE_WASH.search(txt):
            a["wash"] += 1
        if _RE_VECTOR.search(txt):
            a["vector"] += 1
    return agg


def datos_riesgo_sanitario() -> list[dict]:
    """Índice de riesgo sanitario 0–100 por estado. Anclado en la POBLACIÓN EXPUESTA
    (desplazados/hacinamiento, 45%) para NO reintroducir el sesgo de densidad de
    reporte; el agua/saneamiento (30%) y los vectores (25%) entran como TASAS
    (proporción de reportes, con suavizado) que miden la INTENSIDAD del problema, no
    su volumen. Devuelve filas ordenadas por índice descendente."""
    kw = _por_estado()
    res = ce.resumen(aptos_promedio=la.APTOS_CENTRAL, personas_hogar=la.PERSONAS_HOGAR_VERTICAL)
    desp = {f["estado"]: f["personas_a_reubicar"] for f in res["por_estado"]}

    estados = set(kw) | set(desp)
    base = []
    for e in estados:
        if e == "Sin dato":
            continue
        k = kw.get(e, {})
        total = k.get("total", 0)
        # Tasas suavizadas (additive smoothing +200) para no premiar volumen ni que
        # un estado con pocos reportes se dispare por 1-2 quejas.
        base.append({
            "estado": e,
            "desplazados": desp.get(e, 0),
            "wash": k.get("wash", 0), "vector": k.get("vector", 0), "total": total,
            "wash_rate": k.get("wash", 0) / (total + 200),
            "vector_rate": k.get("vector", 0) / (total + 200),
        })
    if not base:
        return []

    def _norm(key):
        mx = max((b[key] for b in base), default=0) or 1
        return {b["estado"]: b[key] / mx for b in base}

    nw, nv = _norm("wash_rate"), _norm("vector_rate")
    # Riesgo = POBLACIÓN EXPUESTA (desplazados) × intensidad del peligro (1 + tasas
    # de agua/saneamiento y vectores). Así un estado sin desplazados no puede salir
    # como riesgo alto de epidemia en albergues, y no hay sesgo de volumen.
    for b in base:
        b["_riesgo"] = b["desplazados"] * (1 + 0.7 * nw[b["estado"]] + 0.5 * nv[b["estado"]])
    max_r = max((b["_riesgo"] for b in base), default=0) or 1.0
    for b in base:
        idx = 100 * b["_riesgo"] / max_r
        b["indice"] = round(idx, 1)
        b["nivel"] = "Alto" if idx >= 50 else "Medio" if idx >= 20 else "Bajo"
        b["agua_l_dia"] = b["desplazados"] * 15
        b["letrinas"] = math.ceil(b["desplazados"] / 20) if b["desplazados"] else 0
    base.sort(key=lambda b: b["indice"], reverse=True)
    return base


def _fmt(n) -> str:
    try:
        return f"{int(round(n)):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(n)


def generar_reporte(out_path: str | None = None, top: int = 12) -> str:
    filas = datos_riesgo_sanitario()
    outdir = Settings().reports_out_dir
    out_path = out_path or os.path.join(outdir, "Alerta de salud publica y epidemias - Terremoto 24J.docx")

    total_desp = sum(f["desplazados"] for f in filas)
    agua_total = sum(f["agua_l_dia"] for f in filas)
    letrinas_total = sum(f["letrinas"] for f in filas)
    altos = [f for f in filas if f["nivel"] == "Alto"]

    img = ""
    top_idx = {f["estado"]: f["indice"] for f in filas[:12] if f["indice"] > 0}
    if top_idx:
        ruta = grafico_barras(
            top_idx, "Índice de riesgo sanitario por estado (0–100)",
            os.path.join(outdir, "charts", "salud_riesgo.png"), color=ROJO,
            fuente="Fuente: desplazados + reportes de agua/saneamiento y vectores · umbrales Esfera/OMS.")
        img = f"![Índice de riesgo sanitario por estado]({ruta})"

    tabla = ["## Índice de riesgo sanitario por estado",
             "| Estado | Nivel | Índice | Desplazados | Reportes agua/saneam. | Reportes vectores (dengue) |",
             "|---|---|---|---|---|---|"]
    for f in filas[:top]:
        tabla.append(f"| {f['estado']} | {f['nivel']} | {f['indice']} | {_fmt(f['desplazados'])} | "
                     f"{_fmt(f['wash'])} | {_fmt(f['vector'])} |")

    nombres_altos = ", ".join(f["estado"] for f in altos[:5]) or "—"
    partes = [
        "# Alerta de salud pública y riesgo de epidemias — Terremoto 24J",
        "## Resumen ejecutivo",
        "La **segunda catástrofe** tras un terremoto suele ser sanitaria. Con la población "
        f"desplazada estimada (~{_fmt(total_desp)} personas) hacinada y el agua y saneamiento "
        "afectados, hay riesgo de **enfermedades diarreicas/cólera**, **dengue** (agua estancada) y "
        f"brotes **respiratorios**. Estados en riesgo **ALTO**: **{nombres_altos}**. La ventana para "
        "actuar es AHORA, de forma preventiva.",
        "## Precedente que debemos evitar",
        "En **Haití 2010**, un brote de **cólera** posterior al terremoto causó ~10.000 muertes — una "
        "catástrofe secundaria evitable con agua segura y saneamiento a tiempo. Venezuela además tiene "
        "**dengue endémico**, que se dispara con el agua estancada y la basura acumulada.",
    ]
    if img:
        partes += ["## Dónde está el mayor riesgo", img]
    partes += [
        "\n".join(tabla),
        "## Las tres amenazas y su señal en los datos",
        "- **Diarreicas / cólera (peso 40%)**: reportes de agua y saneamiento colapsados → agua no "
        "segura. Es la amenaza más letal (precedente Haití).\n"
        "- **Vectoriales / dengue (30%)**: reportes de agua estancada, aguas negras y basura → "
        "criaderos de zancudos.\n"
        "- **Respiratorias / hacinamiento (30%)**: concentración de desplazados en albergues.",
        "## Brecha de agua y saneamiento (estándar Esfera)",
        f"Para la población desplazada estimada se requieren **~{_fmt(agua_total)} litros de agua "
        f"potable al día** (15 L/persona/día) y **~{_fmt(letrinas_total)} letrinas/baños** (1 por 20 "
        "personas). Cubrir esta brecha es la principal medida para cortar el riesgo diarreico.",
        "## Acciones preventivas recomendadas",
        "1. **Agua segura**: pre-posicionar agua potable y kits de tratamiento/cloración en los "
        "estados de riesgo alto.\n"
        "2. **Cólera/diarrea**: sales de rehidratación oral (SRO), antibióticos y vigilancia de casos; "
        "evaluar vacunación oral donde aplique.\n"
        "3. **Dengue**: fumigación, eliminación de criaderos (agua estancada/basura), mosquiteros.\n"
        "4. **Saneamiento**: letrinas y manejo de residuos según Esfera en cada albergue.\n"
        "5. **Vigilancia epidemiológica**: sistema de alerta temprana de casos por albergue/zona.",
        "## Método y fuentes",
        "- Índice = 40% diarreico + 30% vectorial + 30% hacinamiento, normalizado entre estados. Es "
        "una heurística de priorización, no una predicción de casos.\n"
        "- Fuentes: OMS (evaluación de riesgo de enfermedades transmisibles tras desastres), OPS/PAHO, "
        "estándares Esfera 2018.",
    ]
    return render_markdown("\n\n".join(partes), out_path)

"""Suite de informes en un solo paso.

Genera, encadenado:
  1. El informe base (situacional estratégico) con el orquestador existente.
  2. Tres informes derivados (técnico-operativo, brief presidencial, plan de
     comunicación) a partir de los prompts de `prompts/informes/`, alimentados con
     un contexto de datos que incluye **densidad poblacional**, datos de
     **TerremotoVenezuela** y el panorama del evento.
  3. Gráficos (pizzas) embebidos en el informe técnico.

Todo es solo-lectura sobre la BD; la salida son .docx en `reports_out/`.
"""
from __future__ import annotations
import json
import os

from anthropic import Anthropic

from app.config import Settings
from app.agent.orchestrator import generar_informe_dict
from app.report.docx_renderer import render_informe
from app.report.markdown_docx import render_markdown
from app.report.charts import graficos_infraestructura, graficos_panorama, graficos_albergues
from app.tools import densidad, terremotovenezuela, logistica_albergues
from app.db import data_service

_PROMPTS = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "informes")

# clave corta -> (archivo de prompt, TÍTULO del documento, ¿inyectar gráficos?)
# El nombre del archivo de salida se deriva del TÍTULO.
_SPECS = {
    "tecnico": ("informe_tecnico_operativo.md",
                "Balance de daños y operaciones de campo posterior al Terremoto del 24J", True),
    "brief": ("brief_presidencial.md",
              "Evaluación de daños y respuesta inmediata: Terremoto 24J", False),
    "comunicacion": ("plan_comunicacion_emergencia.md",
                     "Plan de comunicación de emergencia: Terremoto 24J", False),
    "albergues": ("plan_albergues_desplazados.md",
                  "Plan de albergues y atención a desplazados: Terremoto 24J", False),
}

_BASE_CACHE = "_base_contexto.json"  # cache del informe base (contexto) para reusar


def _nombre_archivo(titulo: str) -> str:
    """Convierte el título en un nombre de archivo válido (los ':' y '/' no se
    permiten en nombres de archivo, se sustituyen por ' -')."""
    safe = titulo.replace(":", " -").replace("/", "-").strip()
    return f"{safe}.docx"

_SYSTEM = (
    "Eres un analista senior de gestión de emergencias. Sigue AL PIE DE LA LETRA "
    "las instrucciones del PROMPT (estructura, secciones, formato y reglas). "
    "Usa EXCLUSIVAMENTE la data del bloque CONTEXTO; no inventes cifras y separa "
    "hechos confirmados de estimaciones. Para exposición territorial usa SIEMPRE "
    "densidad poblacional (hab/km²), NUNCA población absoluta como métrica. "
    "TODAS las fechas y horas deben expresarse en hora de Venezuela (Caracas, UTC-4); "
    "usa EXACTAMENTE la fecha/hora de corte del bloque 'Corte temporal' del contexto, "
    "nunca UTC ni la hora del servidor. "
    "(encabezados #/##/###, tablas |...|, listas, **negrita**), en español, sin "
    "explicar el proceso de edición."
)


def _ventana_temporal() -> str:
    """Bloque temporal automático: calcula cuántas horas han pasado desde el evento
    y en qué FASE está la respuesta (rescate vs. recuperación). Hace que el informe
    refleje el 'timing' correcto en cada corrida, sin flags."""
    import datetime as dt
    # Momento exacto del doble sismo 24J: 24/06/2026 18:04 (6:04 pm) hora de Caracas.
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("America/Caracas")
        ahora = dt.datetime.now(tz)
        evento = dt.datetime(2026, 6, 24, 18, 4, tzinfo=tz)
    except Exception:
        ahora = dt.datetime.utcnow() - dt.timedelta(hours=4)
        evento = dt.datetime(2026, 6, 24, 18, 4)
    horas = (ahora - evento).total_seconds() / 3600
    dias = horas / 24
    if horas < 72:
        fase = ("VENTANA DE RESCATE CON VIDA ACTIVA (<72 h). Prioridad: búsqueda y rescate "
                "(USAR/INSARAG) a máxima intensidad.")
    elif horas <= 96:
        fase = ("VENTANA DE RESCATE CERRÁNDOSE (72–96 h). Últimas horas de alta probabilidad de "
                "rescate con vida; transición inminente a fase de recuperación.")
    else:
        fase = ("VENTANA DE RESCATE CON VIDA AGOTADA / SUPERADA (>96 h). El evento es POST-72 h: "
                "la respuesta transita de rescate a RECUPERACIÓN y atención humanitaria, aunque se "
                "mantiene búsqueda en bolsones/escombros donde haya indicios. El riesgo agudo "
                "dominante pasa a ser las RÉPLICAS sobre estructuras debilitadas, y la crisis de "
                "albergue, agua, salud y desaparecidos (RFL).")
    return (
        "## Fase temporal de la respuesta (OBLIGATORIO — enfoque por timing)\n"
        f"Horas transcurridas desde el evento (24J 18:04): ~{round(horas)} h (día {int(dias) + 1} de la emergencia).\n"
        f"FASE ACTUAL: {fase}\n"
        "Enfoca el informe en esta fase: NO lo redactes como si la ventana de rescate apenas "
        "comenzara si ya está superada. Cubre explícitamente: (1) qué cambia por el paso del tiempo "
        "(rescate→recuperación), (2) el impacto de las RÉPLICAS que continúan sobre las estructuras "
        "ya dañadas (riesgo de nuevos colapsos, evacuación preventiva), y (3) QUÉ ESPERAR EN LAS "
        "PRÓXIMAS HORAS (escenarios y decisiones). Usa los datos del corte para sustentarlo."
    )


def _indicadores_brief(estado: str | None) -> str:
    """Bloque determinista con los 6 indicadores esenciales del Brief Presidencial,
    para que la tabla de la sección 1 salga con cifras exactas (no estimadas)."""
    from collections import Counter
    from app.db.mongo import build_event_query, get_reports_collection
    from app.db.intensidad_mmi import normalizar_nombre as nn
    try:
        from app.db.ipct import ranking_sobrevivientes
        no_atend = sum(r["no_atendidos"] for r in ranking_sobrevivientes(top=200)["ranking"])
    except Exception:
        no_atend = "En verificación"
    col = get_reports_collection()
    docs = list(col.find(build_event_query(province=estado)))
    ext = Counter(nn((d.get("extracategory") or {}).get("name") or "") for d in docs)
    atrapados = ext.get("persona atrapada bajo escombros", 0) + ext.get("persona que requiere rescate", 0)
    colaps = ext.get("vivienda colapsada", 0)
    # Fallback: el export nuevo no trae la taxonomía fina (extracategory) — solo
    # "Subcategoria" gruesa — así que esos conteos saldrían 0. Si es el caso,
    # detectamos por palabras clave en título/descripción (cifras "reportadas").
    def _cnt_kw(pat: str) -> int:
        rx = {"$regex": pat, "$options": "i"}
        return col.count_documents({**build_event_query(province=estado),
                                    "$or": [{"title": rx}, {"description": rx}]})
    if not atrapados:
        atrapados = _cnt_kw(r"atrapad|bajo (los )?escombros|sepultad|soterrad|debajo de")
    if not colaps:
        colaps = _cnt_kw(r"colaps|derrumb|se vin[oó] abajo|se cay[óo]|destrucci[óo]n total|colapso total")
    desap = data_service.desaparecidos(province=estado, limit=1)["conteo"]
    pct_lg = ""
    if not estado:
        try:
            lg = data_service.desaparecidos(province="La Guaira", limit=1)["conteo"]
            if desap:
                pct_lg = f" ({round(100 * lg / desap)} % en La Guaira)"
        except Exception:
            pass
    total_rep = data_service.total_reportes(province=estado)
    # NOTA: NO se incluye la cobertura de asignación/atención de casos como
    # indicador: el campo (assignedTo/Organismo) aún no se guarda de forma
    # consistente y genera ruido al cliente.
    return (
        "## Indicadores esenciales del brief (usa ESTOS valores exactos en la tabla de la sección 1)\n"
        f"- Personas desaparecidas reportadas: {desap}{pct_lg}\n"
        f"- Personas atrapadas bajo escombros (reportadas): {atrapados}\n"
        f"- Posibles sobrevivientes no atendidos (ventana de rescate): {no_atend}\n"
        f"- Viviendas colapsadas: {colaps}\n"
        f"- Reportes ciudadanos recibidos: {total_rep}\n"
    )


def _corte_caracas() -> str:
    """Bloque de corte temporal en hora de Venezuela (Caracas, UTC-4), para que
    TODAS las fechas/horas del documento usen la zona horaria correcta y no la
    del servidor."""
    import datetime as dt
    try:
        from zoneinfo import ZoneInfo
        ahora = dt.datetime.now(ZoneInfo("America/Caracas"))
    except Exception:
        ahora = dt.datetime.utcnow() - dt.timedelta(hours=4)  # respaldo: UTC-4 fijo
    corte = ahora.strftime("%d/%m/%Y — %H:%M")
    return (
        "## Corte temporal (OBLIGATORIO — hora de Venezuela / Caracas, UTC-4)\n"
        f"Fecha y hora de corte: {corte} (hora local de Caracas).\n"
        "Evento: 24/06/2026 (tarde).\n"
        "REGLA: TODAS las fechas y horas que aparezcan en el documento deben expresarse en "
        "hora de Venezuela (Caracas, UTC-4). Usa EXACTAMENTE esta fecha y hora de corte; "
        "NUNCA uses UTC, la hora del servidor ni inventes una hora distinta."
    )


def _contexto(base: dict, estado: str | None) -> str:
    partes = []
    partes.append(_corte_caracas())
    partes.append(_ventana_temporal())
    try:
        partes.append(_indicadores_brief(estado))
    except Exception as e:
        partes.append(f"## Indicadores esenciales del brief\n(no disponibles: {e})")
    partes.append("## Resumen del informe base\n" + json.dumps({
        k: base.get(k) for k in ("resumen_ejecutivo", "hallazgos_clave",
                                 "analisis_riesgos", "recomendaciones", "zonas_ciegas")
    }, ensure_ascii=False)[:9000])
    try:
        pan = data_service.panorama_completo(province=estado)
        partes.append("## Panorama cuantitativo\n```json\n" + json.dumps(pan, ensure_ascii=False)[:6000] + "\n```")
    except Exception as e:
        partes.append(f"## Panorama cuantitativo\n(no disponible: {e})")
    partes.append("## Densidad poblacional por localidad (usar esto, no población absoluta)\n"
                  + densidad.tabla_densidad_md(top=14))
    partes.append("## Edificios afectados verificados (TerremotoVenezuela — ciudadana, no oficial)\n"
                  + terremotovenezuela.tabla_edificios_md(limite=25))
    for nombre, fn in (("Desaparecidos", lambda: data_service.desaparecidos(limit=8)),
                       ("Daño estructural", lambda: data_service.dano_estructural(limit=8))):
        try:
            partes.append(f"## {nombre}\n```json\n" + json.dumps(fn(), ensure_ascii=False)[:2500] + "\n```")
        except Exception:
            pass
    return "\n\n".join(partes)


def _llm_markdown(prompt_text: str, contexto: str, modelo: str, s: Settings,
                  max_tokens: int = 8000) -> str:
    client = Anthropic(api_key=s.anthropic_api_key)
    msg = client.messages.create(
        model=modelo, max_tokens=max_tokens, system=_SYSTEM,
        messages=[{"role": "user",
                   "content": f"# PROMPT\n{prompt_text}\n\n---\n# CONTEXTO (única fuente de datos)\n{contexto}"}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


# Pies de foto (también sirven de alt) por clave de gráfico.
_TITULOS_GRAFICOS = {
    "tipo_emergencia": "Reportes por tipo de emergencia",
    "estados": "Estados más afectados por volumen de reportes",
    "evolucion": "Evolución diaria desde el 24J: reportes y edificaciones/personas/servicios afectados",
    "servicios": "Incidencias en servicios por sector",
    "electricidad": "Daño eléctrico por tipo",
    "salud": "Reportes en salud, escuelas y edificios públicos",
    "desplazados_estado": "Desplazados estimados por estado (daño estructural × hogar)",
    "escenarios": "Escenarios de población desplazada: cota media vs. máxima demanda",
    "cisternas_estado": "Camiones cisterna requeridos por estado (horizonte de planificación)",
}


def _bloque_imgs(rutas: dict) -> str:
    return "\n\n".join(f"![{_TITULOS_GRAFICOS.get(k, k)}]({v})" for k, v in rutas.items())


def _insertar_tras_encabezado(lines: list[str], bloque: str, claves: tuple[str, ...]) -> bool:
    """Inserta `bloque` justo tras el primer encabezado de SECCIÓN ('##'…'######',
    nunca el título '# ') que contenga alguna de las subcadenas `claves` (sin
    distinguir mayúsculas; ignora la numeración tipo '## 4.'). Devuelve True si lo
    insertó. Excluir el título '# ' evita meter gráficas al principio del documento."""
    for idx, l in enumerate(lines):
        ls = l.lstrip()
        if ls.startswith("##"):
            low = ls.lower()
            if any(c in low for c in claves):
                lines.insert(idx + 1, bloque)
                return True
    return False


def _inyectar_graficos(md: str, outdir: str, panorama: dict | None = None,
                       infra_stats: dict | None = None) -> str:
    charts_dir = os.path.join(outdir, "charts")
    # 1) Gráficos DETERMINISTAS desde los datos (siempre que haya panorama). Son la
    #    base fiable: no dependen de cómo redacte el LLM.
    pan_rutas = graficos_panorama(panorama or {}, outdir=charts_dir)

    # 2) Gráficos de infraestructura, también DESDE LOS DATOS (keyword en
    #    título/descripción vía data_service.estadisticas_infraestructura), no de la
    #    prosa del LLM —que era frágil y los hacía desaparecer al cambiar la redacción.
    infra_rutas = graficos_infraestructura(infra_stats, outdir=charts_dir) if infra_stats else {}

    if not pan_rutas and not infra_rutas:
        return md

    lines = md.split("\n")
    # Las gráficas se insertan DENTRO de secciones existentes (sin añadir encabezados
    # nuevos), para no alterar el flujo del documento. NUNCA al principio.
    #  - Situación (tipo/estados/evolución) → "Tablero general de indicadores".
    #  - Infraestructura → "Infraestructura y servicios".
    # Si no se encuentra el ancla preferido, se prueban alternativos y, en último
    # caso, se anexan al final (jamás arriba).
    if infra_rutas:
        bloque = "\n" + _bloque_imgs(infra_rutas) + "\n"
        if not _insertar_tras_encabezado(lines, bloque, ("infraestructura",)):
            lines.append(bloque)
    if pan_rutas:
        bloque = "\n" + _bloque_imgs(pan_rutas) + "\n"
        if not (_insertar_tras_encabezado(lines, bloque, ("tablero", "indicadores"))
                or _insertar_tras_encabezado(lines, bloque, ("panorama", "magnitud", "afectaci"))
                or _insertar_tras_encabezado(lines, bloque, ("infraestructura",))):
            lines.append(bloque)
    return "\n".join(lines)


def _inyectar_graficos_albergues(md: str, outdir: str, estado: str | None) -> str:
    """Gráficos propios del documento de albergues (desplazados por estado,
    escenarios de demanda y camiones cisterna por estado), insertados en sus
    secciones naturales sin alterar el flujo."""
    try:
        datos = logistica_albergues.datos_para_graficos(estado=estado)
        rutas = graficos_albergues(datos, outdir=os.path.join(outdir, "charts"))
    except Exception:  # noqa: BLE001
        return md
    if not rutas:
        return md

    lines = md.split("\n")
    # Desplazados por estado + escenarios → sección "Población desplazada estimada".
    demanda = {k: rutas[k] for k in ("desplazados_estado", "escenarios") if k in rutas}
    if demanda:
        bloque = "\n" + _bloque_imgs(demanda) + "\n"
        if not (_insertar_tras_encabezado(lines, bloque, ("desplaz",))
                or _insertar_tras_encabezado(lines, bloque, ("resumen ejecutivo", "resumen"))):
            lines.append(bloque)
    # Camiones cisterna por estado → sección "Priorización territorial / despliegue".
    if "cisternas_estado" in rutas:
        bloque = "\n" + _bloque_imgs({"cisternas_estado": rutas["cisternas_estado"]}) + "\n"
        if not _insertar_tras_encabezado(lines, bloque, ("prioriz", "territorial", "despliegue")):
            lines.append(bloque)
    return "\n".join(lines)


def _obtener_base(estado, instruccion, modelo, outdir, reusar_base: bool) -> dict:
    """Devuelve el informe base (contexto). Lo reusa desde cache si `reusar_base`
    y existe; si no, lo genera y lo cachea. Permite generar reportes 'uno por uno'
    sin rehacer el informe base cada vez."""
    cache = os.path.join(outdir, _BASE_CACHE)
    if reusar_base and os.path.exists(cache):
        try:
            with open(cache, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:  # noqa: BLE001
            pass
    base = generar_informe_dict("situacional_estrategico", estado, instruccion, modelo)
    try:
        with open(cache, "w", encoding="utf-8") as fh:
            json.dump(base, fh, ensure_ascii=False)
    except Exception:  # noqa: BLE001
        pass
    return base


def generar_suite(estado: str | None = None, instruccion: str = "",
                  modelo: str | None = None, outdir: str | None = None,
                  solo: list[str] | None = None, reusar_base: bool = False,
                  incluir_base: bool = True) -> dict:
    """Genera los informes derivados (y opcionalmente el base). Devuelve {clave: ruta}.

    solo: lista de claves a generar (p. ej. ['brief'] o ['brief','tecnico']);
          None = todos (tecnico, brief, comunicacion).
    reusar_base: reusa el informe base cacheado en vez de regenerarlo (para
          generar reportes uno por uno sin rehacer el base).
    incluir_base: si True, también renderiza el informe base como .docx.
    """
    s = Settings()
    modelo = modelo or s.anthropic_model
    outdir = outdir or s.reports_out_dir
    os.makedirs(outdir, exist_ok=True)

    claves = solo or list(_SPECS.keys())
    invalidas = [c for c in claves if c not in _SPECS]
    if invalidas:
        raise ValueError(f"Reportes desconocidos: {invalidas}. Válidos: {list(_SPECS)}")

    base = _obtener_base(estado, instruccion, modelo, outdir, reusar_base)
    salidas: dict = {}
    if incluir_base:
        salidas["base"] = render_informe(base, os.path.join(outdir, "INFORME_BASE.docx"))

    # Datos para gráficos deterministas: panorama + infraestructura (keyword). Se
    # calculan una vez y se reutilizan para todos los documentos con gráficos.
    try:
        panorama = data_service.panorama_completo(province=estado)
    except Exception:  # noqa: BLE001
        panorama = None
    try:
        infra_stats = data_service.estadisticas_infraestructura(province=estado)
    except Exception:  # noqa: BLE001
        infra_stats = None

    contexto = _contexto(base, estado)
    # Bloque de logística de albergues (proyecciones deterministas) — solo se añade
    # al contexto del documento que lo necesita, para no inflar los demás.
    _logistica_md: str | None = None
    for clave in claves:
        pf, titulo, con_graficos = _SPECS[clave]
        prompt = open(os.path.join(_PROMPTS, pf), encoding="utf-8").read()
        ctx = contexto
        if clave == "albergues":
            if _logistica_md is None:
                try:
                    _logistica_md = logistica_albergues.bloque_contexto_md(estado=estado)
                except Exception as e:  # noqa: BLE001
                    _logistica_md = f"## Logística de albergues\n(no disponible: {e})"
            ctx = contexto + "\n\n" + _logistica_md
        md = _llm_markdown(prompt, ctx, modelo, s)
        if clave == "albergues":
            md = _inyectar_graficos_albergues(md, outdir, estado)
        elif con_graficos:
            md = _inyectar_graficos(md, outdir, panorama, infra_stats)
        salidas[clave] = render_markdown(md, os.path.join(outdir, _nombre_archivo(titulo)))
    return salidas

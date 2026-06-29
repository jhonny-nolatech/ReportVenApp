"""Orquestador: el loop agéntico del Copiloto Estratégico.

Ejecuta el loop de tool use de Anthropic, deja que Claude consulte
datos/web/conocimiento y termina cuando llama `entregar_informe`. Devuelve un
`Informe` validado. Nunca escribe en la BD ni expone PII individual.
"""
from __future__ import annotations

import datetime as dt
import json
import logging

from anthropic import Anthropic

from app.agent.schema import TIPOS_REPORTE, Informe, validar_informe
from app.agent.tools_def import TOOLS, ejecutar_tool
from app.config import Settings

logger = logging.getLogger("copiloto.orchestrator")


def _ahora_caracas() -> str:
    """Fecha y hora actual en Venezuela (Caracas, UTC-4), formato ISO a minutos."""
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo("America/Caracas")).strftime("%Y-%m-%d %H:%M")
    except Exception:  # noqa: BLE001 — respaldo: UTC-4 fijo
        return (dt.datetime.utcnow() - dt.timedelta(hours=4)).strftime("%Y-%m-%d %H:%M")

# Límite de tamaño por tool_result para no inflar el contexto.
_MAX_TOOL_RESULT = 120_000

SYSTEM_PROMPT = (
    "Eres el **Copiloto Estratégico** de un comité nacional de gestión de crisis tras el "
    "**Terremoto 24J** en Venezuela (sismo del 24 de junio de 2026). Tu misión NO es solo reportar "
    "estadísticas: es pensar como un comité de crisis de primer nivel. Para cada informe debes "
    "aportar: panorama de datos, análisis de **riesgos**, **predicciones**, **casos análogos** "
    "internacionales, **protocolos** recomendados (FEMA, ONU/OCHA/INSARAG, Esfera, Cruz Roja, "
    "Protección Civil), **recomendaciones** priorizadas, **acciones preventivas** e **indicadores "
    "nuevos** que el comité podría adoptar. Genera ideas proactivamente.\n\n"
    "Método obligatorio:\n"
    "1. Llama SIEMPRE primero a `obtener_panorama_estadistico` para fundamentar todo en datos reales.\n"
    "2. Llama SIEMPRE a `consultar_zonas_silenciosas` para detectar PUNTOS CIEGOS (zonas de alta "
    "intensidad MMI y mucha población con pocos o cero reportes). Es obligatorio para mitigar el "
    "sesgo de no-reporte. Reporta el ranking con cifras exactas (MMI, población, reportes "
    "observados vs esperados, cobertura) en `zonas_ciegas` y `resumen_puntos_ciegos`.\n"
    "3. Llama SIEMPRE a `consultar_vulnerabilidad` (nivel estado y, según el foco, municipio/"
    "parroquia) para priorizar EN FUNCIÓN DE LA CANTIDAD DE PERSONAS (afectación per cápita 0–100 %). "
    "En números absolutos manda Caracas por población, pero per cápita domina La Guaira (Vargas/"
    "Caraballeda): refleja esta distinción explícitamente y prioriza las zonas más afectadas por "
    "habitante. Cita las cifras (vulnerabilidad %, desaparecidos, colapsadas) en hallazgos y tablas.\n"
    "4. Usa `obtener_muestra_reportes` para color cualitativo cuando aporte.\n"
    "5. Usa `consultar_conocimiento` para protocolos y casos país; y `buscar_web` para actualizar/"
    "verificar y traer lecciones recientes (cita la url).\n"
    "6. Cuando tengas evidencia suficiente, redacta el informe y entrégalo con `entregar_informe`.\n\n"
    "FORMATO EJECUTIVO (OBLIGATORIO): este informe es para la **Presidenta de la República** y su "
    "comité. La lectura debe ser RÁPIDA y FRESCA, con lo más importante en las primeras páginas. "
    "Estructura priorizada: (1) `hallazgos_clave` — bullets con TODO lo importante (hechos y cifras "
    "clave, frases cortas y contundentes; 6-10 viñetas); (2) `recomendaciones` priorizadas P1/P2/P3; "
    "(3) `conclusiones` — cierre ejecutivo de 3-5 frases orientadas a la decisión; "
    "(4) `plan_comunicaciones` — PLAN DE MEDIOS y mensajería de crisis: define `objetivo` "
    "comunicacional, `voceria` (quién comunica oficialmente), una lista de `mensajes_alerta` "
    "CONCRETOS para difundir a la población (cada uno con `canal` —TV, Radio, SMS, Redes, "
    "Perifoneo/megáfono, Línea 58—, `audiencia`, `mensaje` textual claro/accionable/sin generar "
    "pánico, y `momento`/frecuencia) y `lineamientos` (qué comunicar y qué evitar; cómo canalizar a "
    "familiares de desaparecidos vía RFL; combatir rumores). El resto (panorama, zonas ciegas, "
    "riesgos, predicciones, casos, protocolos) es el DESARROLLO que va después. "
    "SIEMPRE llena `hallazgos_clave`, `conclusiones` y `plan_comunicaciones`.\n\n"
    "Reglas:\n"
    "- Todo dato cuantitativo debe venir de las herramientas, nunca inventado. Si no hay dato, dilo.\n"
    "- Cada riesgo debe citar la evidencia de datos que lo respalda (`evidencia_datos`).\n"
    "- Las recomendaciones deben ser concretas, accionables y priorizadas (P1/P2/P3).\n"
    "- REGLA RECTORA de puntos ciegos: 'sin reportes' NUNCA significa 'sin problema'. Una zona de "
    "alta intensidad y población con baja recepción es una ZONA DE ATENCIÓN y debe priorizarse para "
    "verificación en terreno. Separa hecho de inferencia (no afirmes daño como certeza), pero SÍ "
    "eleva la prioridad. Redacta el mensaje rector: 'según el cruce, en <lugar> la intensidad fue "
    "<MMI> y hasta ahora no hay reportes; según protocolos y casos comparables es muy probable una "
    "tragedia mayor: priorizar'.\n"
    "- Parafrasea siempre las fuentes web; nunca copies texto literal; incluye urls en `fuentes`.\n"
    "- Trata la PII con cuidado: trabaja con agregados; nunca expongas datos personales individuales.\n"
    "- Escribe en español claro, institucional y orientado a la decisión."
)


def generar_informe(tipo: str, estado: str | None = None,
                    instruccion_adicional: str = "",
                    modelo: str | None = None,
                    max_iter: int = 14) -> Informe:
    s = Settings().validate()
    client = Anthropic(api_key=s.anthropic_api_key)
    modelo = modelo or s.anthropic_model

    tipo_info = TIPOS_REPORTE.get(tipo, TIPOS_REPORTE["situacional_estrategico"])
    # Instrucción incorporada del tipo (enfoque fijo) + la extra del usuario.
    instruccion_tipo = tipo_info.get("instruccion", "")
    instruccion_efectiva = "\n".join(
        p for p in (instruccion_tipo, instruccion_adicional) if p
    ) or "(ninguna)"
    user_msg = (
        f"Genera un informe del tipo: **{tipo_info['label']}**.\n"
        f"Descripción del tipo: {tipo_info['descripcion']}\n"
        f"{'Estado/provincia de enfoque: ' + estado if estado else 'Cobertura: nacional.'}\n"
        f"Instrucción adicional del usuario: {instruccion_efectiva}\n"
        f"Fecha de generación (hora de Venezuela/Caracas, UTC-4): {_ahora_caracas()}. "
        f"Usa SIEMPRE hora de Caracas en el informe, nunca UTC ni hora del servidor.\n"
        "Recuerda: fundamenta en datos reales (usa las herramientas) y entrega con 'entregar_informe'."
    )

    messages: list[dict] = [{"role": "user", "content": user_msg}]

    for i in range(max_iter):
        resp = client.messages.create(
            model=modelo,
            max_tokens=20000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        # Recolecta los tool_use de la respuesta, sea cual sea el stop_reason.
        # (Si stop_reason == 'max_tokens', el bloque puede venir incompleto: hay que
        # responder igual cada tool_use con un tool_result o la API rechaza el turno.)
        tool_uses = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]

        if not tool_uses:
            logger.info("iter %d: stop_reason=%s (empujando a entregar)", i, resp.stop_reason)
            messages.append({"role": "user", "content":
                "Debes entregar el informe llamando a la herramienta 'entregar_informe'."})
            continue

        if resp.stop_reason == "max_tokens":
            logger.warning("iter %d: respuesta truncada por max_tokens", i)

        tool_results = []
        for block in tool_uses:
            logger.info("iter %d: tool=%s", i, block.name)
            if block.name == "entregar_informe":
                # Señal terminal: validar y devolver.
                return validar_informe(block.input)
            try:
                out = ejecutar_tool(block.name, block.input)
            except Exception as e:  # noqa: BLE001 — no romper el loop
                logger.warning("iter %d: error en tool %s: %s", i, block.name, e)
                out = {"error": str(e)}
            payload = json.dumps(out, ensure_ascii=False, default=str)
            if len(payload) > _MAX_TOOL_RESULT:
                payload = payload[:_MAX_TOOL_RESULT] + '… [TRUNCADO]"}'
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": payload,
            })
        if tool_results:
            messages.append({"role": "user", "content": tool_results})

    raise RuntimeError("El agente no entregó el informe dentro del límite de iteraciones.")


def generar_informe_dict(tipo: str, estado: str | None = None,
                         instruccion_adicional: str = "",
                         modelo: str | None = None,
                         max_iter: int = 14) -> dict:
    """Igual que `generar_informe` pero devuelve `dict` (lo usa la API y el renderer)."""
    informe = generar_informe(tipo, estado, instruccion_adicional, modelo, max_iter)
    return informe.model_dump()

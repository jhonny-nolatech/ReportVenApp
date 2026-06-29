# Paso 08 — Orquestador (loop agéntico del Copiloto Estratégico)

## Objetivo
Crear `app/agent/orchestrator.py`: el cerebro. Ejecuta el loop de tool use de Anthropic, deja que
Claude consulte datos/web/conocimiento, y termina cuando llama `entregar_informe`. Devuelve un
`Informe` validado.

## Especificación

### System prompt (constante `SYSTEM_PROMPT`)
Redáctalo en español, con este espíritu (puedes mejorarlo, pero conserva el rol y las reglas):

> Eres el **Copiloto Estratégico** de un comité nacional de gestión de crisis tras el **Terremoto
> 24J** en Venezuela (sismo del 24 de junio de 2026). Tu misión NO es solo reportar estadísticas:
> es pensar como un comité de crisis de primer nivel. Para cada informe debes aportar:
> panorama de datos, análisis de **riesgos**, **predicciones**, **casos análogos** internacionales,
> **protocolos** recomendados (FEMA, ONU/OCHA/INSARAG, Esfera, Cruz Roja, Protección Civil),
> **recomendaciones** priorizadas, **acciones preventivas** e **indicadores nuevos** que el comité
> podría adoptar. Genera ideas proactivamente.
>
> Método obligatorio:
> 1. Llama SIEMPRE primero a `obtener_panorama_estadistico` para fundamentar todo en datos reales.
> 2. Usa `obtener_muestra_reportes` para color cualitativo cuando aporte.
> 3. Usa `consultar_conocimiento` para protocolos y casos país; y `buscar_web` para actualizar/
>    verificar y traer lecciones recientes (cita la url).
> 4. Cuando tengas evidencia suficiente, redacta el informe y entrégalo con `entregar_informe`.
>
> Reglas:
> - Todo dato cuantitativo debe venir de las herramientas, nunca inventado. Si no hay dato, dilo.
> - Cada riesgo debe citar la evidencia de datos que lo respalda (`evidencia_datos`).
> - Las recomendaciones deben ser concretas, accionables y priorizadas (P1/P2/P3).
> - Parafrasea siempre las fuentes web; nunca copies texto literal; incluye urls en `fuentes`.
> - Trata la PII con cuidado: trabaja con agregados; nunca expongas datos personales individuales.
> - Escribe en español claro, institucional y orientado a la decisión.

### Función principal
```python
import json, datetime as dt
from anthropic import Anthropic
from app.config import Settings
from app.agent.tools_def import TOOLS, ejecutar_tool
from app.agent.schema import validar_informe, TIPOS_REPORTE, Informe

def generar_informe(tipo: str, estado: str | None = None,
                    instruccion_adicional: str = "",
                    modelo: str | None = None,
                    max_iter: int = 14) -> Informe:
    s = Settings()
    client = Anthropic(api_key=s.anthropic_api_key)
    modelo = modelo or s.anthropic_model

    tipo_info = TIPOS_REPORTE.get(tipo, TIPOS_REPORTE["situacional_estrategico"])
    user_msg = (
        f"Genera un informe del tipo: **{tipo_info['label']}**.\n"
        f"Descripción del tipo: {tipo_info['descripcion']}\n"
        f"{'Estado/provincia de enfoque: ' + estado if estado else 'Cobertura: nacional.'}\n"
        f"Instrucción adicional del usuario: {instruccion_adicional or '(ninguna)'}\n"
        f"Fecha de generación: {dt.datetime.now().isoformat(timespec='minutes')}.\n"
        "Recuerda: fundamenta en datos reales (usa las herramientas) y entrega con 'entregar_informe'."
    )

    messages = [{"role": "user", "content": user_msg}]

    for _ in range(max_iter):
        resp = client.messages.create(
            model=modelo,
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason != "tool_use":
            # El modelo no pidió tool: empújalo a entregar.
            messages.append({"role": "user", "content":
                "Debes entregar el informe llamando a la herramienta 'entregar_informe'."})
            continue

        tool_results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            if block.name == "entregar_informe":
                # señal terminal: validar y devolver
                return validar_informe(block.input)
            try:
                out = ejecutar_tool(block.name, block.input)
            except Exception as e:
                out = {"error": str(e)}
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(out, ensure_ascii=False, default=str)[:120000],
            })
        if tool_results:
            messages.append({"role": "user", "content": tool_results})

    raise RuntimeError("El agente no entregó el informe dentro del límite de iteraciones.")
```

Requisitos adicionales:
- El modelo por defecto sale de `Settings().anthropic_model` (`claude-sonnet-4-6`). Permitir pasar
  `modelo` (p. ej. `claude-opus-4-8` para informes más exigentes).
- Recortar el `content` de cada `tool_result` a un tamaño seguro (evitar inflar el contexto: el
  panorama puede ser grande; truncar muestras/geo si hiciera falta y dejar nota).
- Manejar `default=str` en `json.dumps` por si quedaran tipos no serializables.
- Logging básico (qué tool se llamó en cada iteración) con `logging`, sin imprimir PII.
- Exponer también `generar_informe_dict(...) -> dict` que devuelva `informe.model_dump()` (lo usará
  la API y el renderer).

## Criterios de aceptación
- `from app.agent.orchestrator import generar_informe` importa sin error.
- Una corrida real `generar_informe("resumen_ejecutivo")` devuelve un `Informe` válido con
  `resumen_ejecutivo` no vacío y al menos 1 recomendación. (Probar con poco `max_tokens`/modelo
  Sonnet para abaratar.)
- El loop nunca escribe en la BD ni expone PII individual.

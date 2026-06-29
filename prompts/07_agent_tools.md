# Paso 07 — Tools del agente (definición Anthropic + dispatcher)

## Objetivo
Crear `app/agent/tools_def.py`: las definiciones de herramientas que verá Claude (formato de la
Messages API de Anthropic) y un **dispatcher** que ejecuta cada tool llamando a las capas ya
construidas (data_service, serper, knowledge_base) y al tool final de entrega.

## Contexto
El agente trabaja con tool use. Cinco herramientas:
1. `obtener_panorama_estadistico` → `data_service.panorama_completo(...)`
2. `obtener_muestra_reportes` → `data_service.muestra_reportes(...)`
3. `buscar_web` → `serper.buscar_web(...)`
4. `consultar_conocimiento` → `knowledge_base.consultar_conocimiento(...)` (+ `listar_temas`)
5. `entregar_informe` → tool **terminal**: su input ES el JSON del `Informe` (paso 06). Cuando el
   agente la llama, el loop captura ese payload, lo valida y termina.

## Especificación

### `app/agent/tools_def.py`

```python
from app.db import data_service
from app.tools import serper, knowledge_base
from app.agent.schema import Informe

TOOLS = [
  {
    "name": "obtener_panorama_estadistico",
    "description": ("Devuelve el panorama cuantitativo COMPLETO del Terremoto 24J desde la base de "
        "datos de reportes ciudadanos: total, por estado de gestión, por tipo de emergencia "
        "(extracategoría), por estado/municipio, evolución temporal, cobertura de asignación, "
        "personas desaparecidas y daño estructural. Úsalo SIEMPRE primero para fundamentar el informe. "
        "Filtra por 'estado' (provincia) solo si el informe es geográfico."),
    "input_schema": {
        "type": "object",
        "properties": {
            "estado": {"type": "string", "description": "Nombre del estado/provincia para acotar (opcional)."}
        },
    },
  },
  {
    "name": "obtener_muestra_reportes",
    "description": ("Devuelve una muestra de reportes reales (texto de título/descripción) para dar "
        "color cualitativo. PII redactada por defecto. focus: 'desaparecidos', 'dano_estructural' o "
        "'general'."),
    "input_schema": {
        "type": "object",
        "properties": {
            "focus": {"type": "string", "enum": ["desaparecidos", "dano_estructural", "general"]},
            "estado": {"type": "string"},
            "limit": {"type": "integer", "default": 15},
        },
        "required": ["focus"],
    },
  },
  {
    "name": "buscar_web",
    "description": ("Búsqueda web (Serper) para protocolos vigentes, noticias del sismo, lecciones "
        "de terremotos análogos y estándares internacionales. Devuelve título, url, snippet. "
        "Parafrasea y cita la url; no copies texto literal."),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "num": {"type": "integer", "default": 6},
        },
        "required": ["query"],
    },
  },
  {
    "name": "consultar_conocimiento",
    "description": ("Base de conocimiento curada: marcos internacionales (FEMA/ICS, ONU/INSARAG, "
        "Esfera, Cruz Roja/RFL, Protección Civil) y casos país (Turquía 2023, Chile 2010, Japón "
        "2011, México 2017, Ecuador 2016) e indicadores. Llama primero con seccion='__temas__' "
        "para ver qué hay disponible."),
    "input_schema": {
        "type": "object",
        "properties": {
            "seccion": {"type": "string", "description": "'protocolos' | 'casos_pais' | 'indicadores' | '__temas__'"},
            "clave": {"type": "string", "description": "clave específica dentro de la sección (opcional)"},
        },
        "required": ["seccion"],
    },
  },
  {
    "name": "entregar_informe",
    "description": ("Entrega el informe FINAL ya redactado y estructurado. Llama a esta herramienta "
        "UNA sola vez, al final, cuando tengas suficiente evidencia de las otras herramientas. El "
        "input debe cumplir EXACTAMENTE el esquema del informe."),
    "input_schema": Informe.model_json_schema(),
  },
]
```

### Dispatcher
```python
def ejecutar_tool(name: str, args: dict) -> dict:
    if name == "obtener_panorama_estadistico":
        return data_service.panorama_completo(province=args.get("estado"))
    if name == "obtener_muestra_reportes":
        return {"reportes": data_service.muestra_reportes(
            focus=args["focus"], province=args.get("estado"),
            limit=args.get("limit", 15), include_pii=False)}
    if name == "buscar_web":
        return serper.buscar_web(args["query"], num=args.get("num", 6))
    if name == "consultar_conocimiento":
        if args["seccion"] == "__temas__":
            return knowledge_base.listar_temas()
        return knowledge_base.consultar_conocimiento(args["seccion"], args.get("clave"))
    raise ValueError(f"Tool desconocida: {name}")
```

Notas:
- `entregar_informe` NO se ejecuta en el dispatcher: el orquestador (paso 08) la intercepta como
  señal de terminación y valida su input con `validar_informe`.
- Todos los resultados de tools deben ser serializables a JSON (ya lo garantiza data_service).
- Si una tool falla, devolver `{"error": "..."}` en lugar de lanzar (no romper el loop).

## Criterios de aceptación
- `from app.agent.tools_def import TOOLS, ejecutar_tool` importa sin error.
- `ejecutar_tool("consultar_conocimiento", {"seccion": "__temas__"})` devuelve las secciones.
- `TOOLS[-1]["name"] == "entregar_informe"` y su `input_schema` es el del modelo `Informe`.

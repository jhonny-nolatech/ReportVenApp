"""Definición de tools para Claude (Messages API) + dispatcher de ejecución.

Cinco herramientas:
  1. obtener_panorama_estadistico → data_service.panorama_completo
  2. obtener_muestra_reportes      → data_service.muestra_reportes
  3. buscar_web                    → serper.buscar_web
  4. consultar_conocimiento        → knowledge_base (+ listar_temas)
  5. entregar_informe              → tool TERMINAL: su input ES el JSON del Informe.
     NO se ejecuta aquí; el orquestador (paso 08) la intercepta, valida y termina.
"""
from __future__ import annotations

from app.agent.schema import Informe
from app.db import data_service
from app.tools import knowledge_base, serper

TOOLS = [
    {
        "name": "obtener_panorama_estadistico",
        "description": (
            "Devuelve el panorama cuantitativo COMPLETO del Terremoto 24J desde la base de datos "
            "de reportes ciudadanos: total, por estado de gestión, por tipo de emergencia "
            "(extracategoría), por estado/municipio, evolución temporal, cobertura de asignación, "
            "personas desaparecidas y daño estructural. Úsalo SIEMPRE primero para fundamentar el "
            "informe. Filtra por 'estado' (provincia) solo si el informe es geográfico."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "estado": {
                    "type": "string",
                    "description": "Nombre del estado/provincia para acotar (opcional).",
                }
            },
        },
    },
    {
        "name": "obtener_muestra_reportes",
        "description": (
            "Devuelve una muestra de reportes reales (texto de título/descripción) para dar color "
            "cualitativo. PII redactada por defecto. focus: 'desaparecidos', 'dano_estructural' o "
            "'general'."
        ),
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
        "description": (
            "Búsqueda web (Serper) para protocolos vigentes, noticias del sismo, lecciones de "
            "terremotos análogos y estándares internacionales. Devuelve título, url, snippet. "
            "Parafrasea y cita la url; no copies texto literal."
        ),
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
        "description": (
            "Base de conocimiento curada: marcos internacionales (FEMA/ICS, ONU/INSARAG, Esfera, "
            "Cruz Roja/RFL, Protección Civil) y casos país (Turquía 2023, Chile 2010, Japón 2011, "
            "México 2017, Ecuador 2016) e indicadores. Llama primero con seccion='__temas__' para "
            "ver qué hay disponible."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "seccion": {
                    "type": "string",
                    "description": "'protocolos' | 'casos_pais' | 'indicadores' | '__temas__'",
                },
                "clave": {
                    "type": "string",
                    "description": "clave específica dentro de la sección (opcional)",
                },
            },
            "required": ["seccion"],
        },
    },
    {
        "name": "consultar_zonas_silenciosas",
        "description": (
            "Cruza la intensidad sísmica MMI por localidad (con población) contra los reportes "
            "recibidos para detectar PUNTOS CIEGOS: zonas de alta intensidad y mucha población con "
            "pocos o cero reportes, que probablemente tienen comunicaciones caídas y necesitan ayuda "
            "urgente. Devuelve un ranking priorizado de zonas críticas, silenciosas y visibles. "
            "REGLA CLAVE: poca señal = ZONA DE ATENCIÓN, NO zona sin problema. Úsala para mitigar el "
            "sesgo de no-reporte y priorizar verificación en terreno."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "umbral_mmi": {"type": "number", "default": 6.0},
                "umbral_habitantes": {"type": "integer", "default": 20000},
                "umbral_cobertura": {"type": "number", "default": 0.25},
                "top": {"type": "integer", "default": 20},
            },
        },
    },
    {
        "name": "consultar_ipct",
        "description": (
            "ÍNDICE DE PRIORIDAD CRÍTICA TERRITORIAL (IPCT), 0–5 por parroquia (5 = máxima "
            "prioridad), calculado de forma DETERMINISTA (no lo estimes tú; usa estas cifras tal "
            "cual). vista='ranking' devuelve el ranking IPCT (Hito 1) con factores: intensidad "
            "sísmica, exposición poblacional, densidad de reportes per cápita y daño/afectación "
            "grave per cápita (la construcción vertical queda pendiente de capa GIS de Chumaceiro). "
            "vista='sobrevivientes' devuelve el cruce de zonas con posibles sobrevivientes NO "
            "atendidos, ordenado por urgencia de rescate (Hito 2, ventana 72–96 h). Úsalo SIEMPRE "
            "como eje del informe de priorización territorial."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "vista": {"type": "string", "enum": ["ranking", "sobrevivientes"]},
                "top": {"type": "integer", "default": 20},
            },
            "required": ["vista"],
        },
    },
    {
        "name": "consultar_vulnerabilidad",
        "description": (
            "Ranking de AFECTACIÓN PER CÁPITA (índice 0–100 % normalizado por población) por "
            "estado/municipio/parroquia, ponderando desaparecidos×4, viviendas colapsadas×2 y casos "
            "críticos. Responde '¿qué entidades están más afectadas EN FUNCIÓN DE LA CANTIDAD DE "
            "PERSONAS?': en números absolutos manda Caracas por su población, pero per cápita domina "
            "La Guaira (Vargas/Caraballeda). Úsalo para priorizar zonas y fundamentar hallazgos y "
            "recomendaciones con cifras de afectación por habitante."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "nivel": {"type": "string", "enum": ["estado", "municipio", "parroquia"]},
                "estado": {"type": "string", "description": "filtra a una entidad (para municipio/parroquia)"},
                "top": {"type": "integer", "default": 15},
            },
            "required": ["nivel"],
        },
    },
    {
        "name": "entregar_informe",
        "description": (
            "Entrega el informe FINAL ya redactado y estructurado. Llama a esta herramienta UNA "
            "sola vez, al final, cuando tengas suficiente evidencia de las otras herramientas. El "
            "input debe cumplir EXACTAMENTE el esquema del informe."
        ),
        "input_schema": Informe.model_json_schema(),
    },
]


def ejecutar_tool(name: str, args: dict) -> dict:
    """Ejecuta una tool de datos/web/conocimiento. `entregar_informe` NO pasa por aquí."""
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
    if name == "consultar_ipct":
        from app.db import ipct
        if args.get("vista") == "sobrevivientes":
            return ipct.ranking_sobrevivientes(top=args.get("top", 20))
        return ipct.ranking_ipct(top=args.get("top", 20))
    if name == "consultar_vulnerabilidad":
        from app.tools import vulnerabilidad
        return vulnerabilidad.consultar_vulnerabilidad(
            nivel=args.get("nivel", "estado"),
            estado=args.get("estado"),
            top=args.get("top", 15),
        )
    if name == "consultar_zonas_silenciosas":
        from app.db.zonas_silenciosas import analizar_puntos_ciegos
        analisis = analizar_puntos_ciegos(
            umbral_mmi=args.get("umbral_mmi", 6.0),
            umbral_habitantes=args.get("umbral_habitantes", 20000),
            umbral_cobertura=args.get("umbral_cobertura", 0.25),
            top=args.get("top", 20),
        )
        return analisis.model_dump(mode="json")  # agregado por localidad; sin PII
    raise ValueError(f"Tool desconocida: {name}")

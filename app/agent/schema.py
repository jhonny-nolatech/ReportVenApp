"""Contrato de datos del informe (Pydantic v2) + catálogo de tipos de reporte.

El agente NO escribe Word: produce un JSON que cumple `Informe`, y un renderer
determinista lo convierte en .docx. Esto garantiza informes consistentes.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class KPI(BaseModel):
    label: str
    valor: str
    nota: str | None = None


class Tabla(BaseModel):
    titulo: str
    columnas: list[str]
    filas: list[list[str]]


class Riesgo(BaseModel):
    riesgo: str
    nivel: Literal["alto", "medio", "bajo"]
    descripcion: str
    evidencia_datos: str | None = None  # qué cifra de la BD lo respalda


class Prediccion(BaseModel):
    horizonte: str  # "24-72 h", "1-2 semanas", etc.
    prediccion: str
    supuestos: str | None = None


class CasoAnalogo(BaseModel):
    pais: str
    evento: str
    leccion: str
    aplicacion_venezuela: str
    fuente: str | None = None


class Protocolo(BaseModel):
    organismo: str  # FEMA, ONU/OCHA, Cruz Roja, Protección Civil...
    protocolo: str
    resumen: str
    fuente: str | None = None


class Recomendacion(BaseModel):
    prioridad: Literal["P1", "P2", "P3"]
    accion: str
    responsable_sugerido: str | None = None
    plazo: str | None = None


class AccionPreventiva(BaseModel):
    accion: str
    justificacion: str


class IndicadorNuevo(BaseModel):
    indicador: str
    definicion: str
    como_calcularlo: str


class MensajeAlerta(BaseModel):
    """Mensaje de alerta/comunicación concreto para difundir a la población."""
    canal: str          # TV, Radio, SMS, Redes, Perifoneo/megáfono, Línea 58...
    audiencia: str      # población La Guaira, familiares de desaparecidos, etc.
    mensaje: str        # texto claro, accionable y sin generar pánico
    momento: str | None = None  # inmediato, cada 6 h, etc.


class PlanComunicaciones(BaseModel):
    """Plan de medios y mensajería de crisis (alertas a la población)."""
    objetivo: str = ""
    voceria: str | None = None  # quién comunica oficialmente
    mensajes_alerta: list[MensajeAlerta] = Field(default_factory=list)
    lineamientos: list[str] = Field(default_factory=list)  # qué comunicar / qué evitar


class Fuente(BaseModel):
    titulo: str
    url: str | None = None


class PanoramaDatos(BaseModel):
    narrativa: str
    kpis: list[KPI] = Field(default_factory=list)
    tablas: list[Tabla] = Field(default_factory=list)


class ZonaCiegaReporte(BaseModel):
    """Zona silenciosa / punto ciego, lista para mostrar en el informe.

    Campos numéricos opcionales (default 0) para no perder un informe casi
    completo si el agente omite alguno en una fila.
    """
    localidad: str
    estado: str | None = None
    mmi: float = 0.0
    habitantes: int = 0
    reportes_observados: int = 0
    reportes_esperados: float = 0.0
    cobertura: float = 0.0
    indice_punto_ciego: float = 0.0
    critica: bool = False
    prioridad: str | None = None  # P1/P2/P3 sugerida por el agente


class MetaInforme(BaseModel):
    titulo: str
    tipo_reporte: str
    fecha_generacion: str
    ventana_datos: str
    preparado_por: str = "Copiloto Estratégico IA — VenApp / Línea 58"
    clasificacion: str = "CONFIDENCIAL — Uso oficial restringido"


class Informe(BaseModel):
    meta: MetaInforme
    resumen_ejecutivo: str
    # Informe EJECUTIVO (para la Presidenta): lo más importante primero.
    hallazgos_clave: list[str] = Field(
        default_factory=list,
        description="Bullets con TODO lo importante: hechos y cifras clave, frases cortas y contundentes.",
    )
    conclusiones: str = Field(
        default="",
        description="Cierre ejecutivo: 3-5 frases claras orientadas a la decisión.",
    )
    plan_comunicaciones: PlanComunicaciones = Field(
        default_factory=PlanComunicaciones,
        description="Plan de medios y mensajes de alerta a la población (estrategia de comunicación de crisis).",
    )
    panorama_datos: PanoramaDatos
    resumen_puntos_ciegos: str = ""
    zonas_ciegas: list[ZonaCiegaReporte] = Field(default_factory=list)
    analisis_riesgos: list[Riesgo] = Field(default_factory=list)
    predicciones: list[Prediccion] = Field(default_factory=list)
    casos_analogos: list[CasoAnalogo] = Field(default_factory=list)
    protocolos_recomendados: list[Protocolo] = Field(default_factory=list)
    recomendaciones: list[Recomendacion] = Field(default_factory=list)
    acciones_preventivas: list[AccionPreventiva] = Field(default_factory=list)
    indicadores_nuevos: list[IndicadorNuevo] = Field(default_factory=list)
    fuentes: list[Fuente] = Field(default_factory=list)
    notas_pii: str = (
        "Este informe puede contener referencias agregadas a datos personales "
        "autodeclarados. Uso oficial restringido; no difundir externamente."
    )


TIPOS_REPORTE = {
    "priorizacion_territorial_ipct": {
        "label": "Priorización Territorial — IPCT, sobrevivientes e infraestructura",
        "descripcion": (
            "Sistema de inteligencia para priorizar la respuesta del gobierno: índice IPCT (0–5) "
            "por parroquia, ranking cruzado con posibles sobrevivientes (ventana 72 h) e "
            "infraestructura básica de atención para las zonas más críticas."
        ),
        "secciones": "ipct",
        "instruccion": (
            "Este informe es un SISTEMA DE INTELIGENCIA PARA PRIORIZACIÓN TERRITORIAL (mandato de "
            "André). El eje son TRES entregables, en este orden: (1) Índice de Prioridad Crítica "
            "Territorial (IPCT) 0–5 por PARROQUIA con ranking; (2) ranking cruzado con POSIBLES "
            "SOBREVIVIENTES no atendidos (ventana crítica 72–96 h); (3) INFRAESTRUCTURA básica de "
            "atención (salud, agua, albergue, alimentación) para parroquias con IPCT ≥ 4.\n"
            "MÉTODO OBLIGATORIO: llama a `consultar_ipct` con vista='ranking' y vista='sobrevivientes' "
            "y usa esas cifras TAL CUAL (el IPCT se calcula determinísticamente, no lo inventes). "
            "Complementa con `consultar_vulnerabilidad` y `obtener_muestra_reportes` (focus "
            "desaparecidos/dano_estructural) para color y nombres de edificios.\n"
            "FRENTE DEL INFORME = inteligencia territorial, priorización y movilización. Con MUCHA "
            "MANO IZQUIERDA: NO pongas al frente recomendaciones obvias para Defensa/Protección Civil "
            "(no digas 'desplieguen radios', 'manden satélites/helicópteros', 'activen "
            "comunicaciones'); si hace falta, exprésalo como 'priorizar mecanismos de confirmación "
            "territorial y comunicación local' y déjalo en el desarrollo, no en los hallazgos.\n"
            "TABLAS (en panorama_datos.tablas): (a) 'Ranking IPCT por parroquia' [Ranking, Estado, "
            "Municipio, Parroquia, IPCT, Nivel, Motivo principal, Reportes, Daños estruct., "
            "Desaparecidos]; (b) 'Prioridad de rescate — posibles sobrevivientes' [Parroquia, Estado, "
            "IPCT, Posibles sobrevivientes, No atendidos, Rescate urgente, Últ. reporte, Acción]; "
            "(c) 'Infraestructura básica (PENDIENTE de validación territorial — Chumaceiro)' con las "
            "parroquias IPCT≥4 y columnas salud/agua/albergue/alimentación = 'Por validar'.\n"
            "HALLAZGOS_CLAVE: las parroquias más críticas por IPCT, dónde hay posibles sobrevivientes "
            "no atendidos, y qué datos faltan validar. RECOMENDACIONES con estructura: dónde actuar, "
            "por qué, qué evidencia (cifras IPCT/reportes), qué infraestructura validar y qué PREGUNTA "
            "CERRADA hacer a la comunidad/responsable local. PLAN_COMUNICACIONES = mensajes con "
            "PREGUNTAS CERRADAS para validar reportes y confirmar infraestructura (no mensajes "
            "genéricos de 'mantenga la calma'). CONCLUSIONES ejecutivas.\n"
            "Incluye SIEMPRE una sección de DATOS PENDIENTES para Alejandro Chumaceiro (capas de "
            "hospitales/ambulatorios, escuelas, polideportivos/gimnasios, posibles albergues, puntos "
            "de agua y zonas con déficit histórico de agua, centros de acopio, cuadrantes validados, "
            "capacidad y estado operativo por zona). Unidad: PARROQUIA (cuadrante donde exista)."
        ),
    },
    "situacional_estrategico": {
        "label": "Situacional estratégico completo",
        "descripcion": (
            "Panorama de datos + riesgos + predicciones + casos análogos + protocolos + "
            "recomendaciones + indicadores."
        ),
        "secciones": "todas",
    },
    "operativo_zonas_criticas": {
        "label": "Operativo — Zonas más afectadas (La Guaira + Miranda/Chacao)",
        "descripcion": (
            "Informe operativo bifocal centrado en las zonas más afectadas: La Guaira "
            "(búsqueda y rescate / desaparecidos) y Miranda con foco en Chacao (daño "
            "estructural). Desglose por municipio y parroquia, sin diluir en cifras nacionales."
        ),
        "secciones": "todas",
        "instruccion": (
            "ENFOQUE PRIORITARIO Y CASI EXCLUSIVO en la ZONA MÁS AFECTADA: el estado LA GUAIRA "
            "(todos sus municipios y parroquias: municipio Vargas y sus parroquias Maiquetía, "
            "Catia La Mar, Caraballeda, La Guaira, Macuto, Naiguatá, Caruao, El Junko, Carayaca) y "
            "el estado MIRANDA, con especial atención al municipio CHACAO. "
            "LA GUAIRA es el epicentro de la TRAGEDIA HUMANA: concentra ~75% de los desaparecidos del "
            "país y los casos de personas atrapadas bajo escombros; trátala como prioridad de búsqueda "
            "y rescate (USAR/INSARAG) y de RFL/Cruz Roja para desaparecidos. MIRANDA concentra el mayor "
            "DAÑO ESTRUCTURAL, con foco en CHACAO. "
            "Método: llama a obtener_panorama_estadistico por SEPARADO para 'La Guaira' y para 'Miranda'; "
            "usa obtener_muestra_reportes con focus='desaparecidos' (La Guaira) y focus='dano_estructural' "
            "(Miranda). Desglosa SIEMPRE por municipio y parroquia. NO diluyas el análisis en cifras "
            "nacionales: el comité necesita un informe OPERATIVO centrado en estas zonas. Recomendaciones "
            "concretas de verificación en terreno, SAR en La Guaira y evaluación estructural en Miranda/Chacao."
        ),
    },
    "resumen_ejecutivo": {
        "label": "Resumen ejecutivo rápido",
        "descripcion": "Versión corta: resumen, 5 KPIs, top riesgos y top recomendaciones.",
        "secciones": "reducidas",
    },
    "foco_desaparecidos": {
        "label": "Foco en personas desaparecidas",
        "descripcion": (
            "Centrado en localización de personas: protocolos RFL/Cruz Roja, distribución "
            "geográfica, acciones."
        ),
        "secciones": "desaparecidos",
    },
    "foco_dano_estructural": {
        "label": "Foco en daño estructural",
        "descripcion": (
            "Edificaciones en riesgo, evaluación de daños, protocolos USAR/FEMA, priorización."
        ),
        "secciones": "estructural",
    },
    "foco_geografico": {
        "label": "Foco geográfico (por estado)",
        "descripcion": "Análisis profundo de un estado/municipio específico.",
        "secciones": "geografico",
    },
    "puntos_ciegos": {
        "label": "Reporte de Zonas Silenciosas / Puntos Ciegos",
        "descripcion": (
            "Foco total en el cruce intensidad sísmica (MMI) × población × reportes recibidos. "
            "Detecta y prioriza zonas de alto impacto sin señal (sesgo de no-reporte): ranking de "
            "zonas críticas, tabla, mapa de puntos ciegos y acciones de verificación en terreno."
        ),
        "secciones": "puntos_ciegos",
    },
}


def validar_informe(data: dict) -> Informe:
    """Parsea/valida el dict del agente; lanza error claro si no cumple el esquema."""
    try:
        return Informe.model_validate(data)
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"El informe del agente no cumple el esquema: {e}") from e

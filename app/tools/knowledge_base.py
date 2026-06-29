"""Base de conocimiento curada (parafraseada) para el comité de crisis.

Marcos de referencia internacionales y lecciones de terremotos análogos. Todo el
texto es resumen propio y parafraseado (nunca copia literal de fuentes); cada
entrada incluye `fuente_oficial` para que el informe pueda citar. La web (Serper)
se usa para actualizar/ampliar; este módulo da el esqueleto sólido y citable.
"""
from __future__ import annotations

KNOWLEDGE = {
    "protocolos": {
        "fema_ics": {
            "organismo": "FEMA (EE. UU.)",
            "titulo": "Sistema de Comando de Incidentes (ICS) y National Response Framework",
            "resumen": (
                "Marco de mando unificado y escalable para gestionar emergencias. Organiza la "
                "respuesta en funciones claras (comando, operaciones, planificación, logística y "
                "administración/finanzas) con cadena de mando definida y tramos de control "
                "manejables. Permite integrar múltiples organismos bajo objetivos comunes y crecer "
                "o reducirse según la magnitud del incidente."
            ),
            "fuente_oficial": "https://www.fema.gov",
        },
        "fema_damage_assessment": {
            "organismo": "FEMA (EE. UU.)",
            "titulo": "Evaluación Preliminar de Daños (PDA)",
            "resumen": (
                "Metodología para clasificar el daño en niveles (afectado, mayor, destruido) "
                "mediante equipos de evaluación en terreno. Sus resultados priorizan la asignación "
                "de recursos, sustentan declaratorias de emergencia y orientan la recuperación."
            ),
            "fuente_oficial": "https://www.fema.gov",
        },
        "onu_insarag": {
            "organismo": "ONU / OCHA — INSARAG",
            "titulo": "Directrices INSARAG para Búsqueda y Rescate Urbano (USAR)",
            "resumen": (
                "Estándar internacional para la búsqueda y rescate en estructuras colapsadas. "
                "Clasifica los equipos USAR (ligero, mediano, pesado), define un sistema común de "
                "marcado de estructuras y víctimas, y coordina la operación in situ mediante el "
                "OSOCC. Subraya la ventana crítica de las primeras 72–96 horas para salvar vidas."
            ),
            "fuente_oficial": "https://www.insarag.org",
        },
        "onu_cluster": {
            "organismo": "ONU / OCHA",
            "titulo": "Sistema de Clusters Humanitarios",
            "resumen": (
                "Modelo de coordinación que agrupa a los actores humanitarios por sectores (salud, "
                "refugio, agua-saneamiento-higiene, logística, protección, seguridad alimentaria, "
                "entre otros), cada uno con una agencia líder. Un coordinador humanitario articula "
                "los clusters para evitar vacíos y duplicidades en la respuesta."
            ),
            "fuente_oficial": "https://www.humanitarianresponse.info",
        },
        "esfera": {
            "organismo": "Sphere",
            "titulo": "Manual Esfera — estándares mínimos humanitarios",
            "resumen": (
                "Conjunto de estándares mínimos para una respuesta digna en agua y saneamiento, "
                "seguridad alimentaria y nutrición, alojamiento y salud, sustentados en una Carta "
                "Humanitaria y principios de protección. Sirve de referencia de calidad y "
                "rendición de cuentas para la ayuda."
            ),
            "fuente_oficial": "https://www.spherestandards.org",
        },
        "mira": {
            "organismo": "IASC / ONU",
            "titulo": "Evaluación Rápida Inicial Multisectorial (MIRA)",
            "resumen": (
                "Proceso conjunto para obtener, en las primeras semanas, una imagen común de las "
                "necesidades prioritarias y de la población afectada cuando aún faltan datos "
                "detallados. Orienta decisiones tempranas con información suficiente y oportuna."
            ),
            "fuente_oficial": "https://www.unocha.org",
        },
        "cruz_roja_rfl": {
            "organismo": "CICR / Cruz Roja",
            "titulo": "Restablecimiento del Contacto entre Familiares (RFL)",
            "resumen": (
                "Servicio para registrar, buscar y reconectar a personas separadas por la "
                "emergencia, incluyendo desaparecidos, y facilitar la reunificación familiar. "
                "Apoya además la gestión digna de información sobre personas fallecidas."
            ),
            "fuente_oficial": "https://familylinks.icrc.org",
        },
        "cruz_roja_aps": {
            "organismo": "IFRC / Cruz Roja",
            "titulo": "Apoyo Psicosocial y Primeros Auxilios Psicológicos",
            "resumen": (
                "Marco de atención al impacto emocional de la crisis sobre damnificados y "
                "respondedores: escucha activa, contención, derivación a servicios especializados "
                "y cuidado del personal de respuesta para prevenir la fatiga y el desgaste."
            ),
            "fuente_oficial": "https://www.ifrc.org",
        },
        "sesgo_no_reporte": {
            "organismo": "Metodología — Copiloto Estratégico",
            "titulo": "Sesgo de no-reporte y mitigación por puntos ciegos",
            "resumen": (
                "Los reportes ciudadanos provienen de donde hay energía, conectividad y población "
                "capaz de reportar. Por eso las zonas MÁS golpeadas suelen ser, precisamente, las "
                "que MENOS reportan: si se prioriza solo sobre lo recibido, la ayuda se desvía lejos "
                "de lo más crítico. Mitigación obligatoria: cruzar la intensidad sísmica (MMI) y la "
                "población por localidad contra los reportes efectivamente recibidos, y publicar "
                "junto a cada análisis el MAPA DE PUNTOS CIEGOS. Toda zona de alta intensidad y "
                "población con baja/nula recepción se trata como ZONA DE ATENCIÓN (no 'zona sin "
                "problema') y se prioriza para verificación en terreno."
            ),
            "fuente_oficial": "Documento del cliente — 'El riesgo que obliga al ajuste: el sesgo de no-reporte'.",
        },
        "proteccion_civil_ve": {
            "organismo": "Protección Civil (Venezuela)",
            "titulo": "Marco de Protección Civil y Administración de Desastres",
            "resumen": (
                "Estructura nacional, regional y municipal para coordinar la respuesta ante "
                "desastres en Venezuela, incluyendo la activación de organismos de seguridad y "
                "rescate y la gestión de albergues y refugios. Conviene verificar la vigencia y "
                "los detalles operativos con fuentes oficiales actualizadas."
            ),
            "fuente_oficial": "https://www.protacioncivil.gob.ve",
        },
    },
    "casos_pais": {
        "turquia_2023": {
            "evento": "Terremotos de Kahramanmaraş, Turquía-Siria",
            "magnitud": "Mw 7.8 y 7.5 (2023)",
            "que_paso": (
                "Doble sismo con decenas de miles de víctimas y colapso masivo de edificaciones, "
                "muchas de construcción informal o sin cumplimiento del código sísmico."
            ),
            "lecciones": (
                "El cumplimiento real del código sísmico es decisivo; la construcción informal "
                "multiplica el colapso; la logística de remoción de escombros y la fatiga de "
                "coordinación condicionan el rescate; la ventana de 72 horas es crítica."
            ),
            "aplicacion_venezuela": (
                "Priorizar la inspección de edificaciones vulnerables e informales y reforzar la "
                "coordinación logística temprana de escombros y maquinaria pesada."
            ),
            "fuente": "https://earthquake.usgs.gov",
        },
        "chile_2010": {
            "evento": "Terremoto del Maule, Chile",
            "magnitud": "Mw 8.8 (2010)",
            "que_paso": (
                "Sismo de gran magnitud seguido de tsunami; pese a la energía liberada, la "
                "mortalidad fue contenida por la calidad constructiva."
            ),
            "lecciones": (
                "Códigos sísmicos estrictos y bien aplicados salvan vidas; hubo fallas en la "
                "alerta de tsunami; la cultura de preparación favoreció una recuperación "
                "relativamente rápida."
            ),
            "aplicacion_venezuela": (
                "Invertir en normas constructivas exigibles y en cadenas de alerta claras hacia "
                "la población costera."
            ),
            "fuente": "https://earthquake.usgs.gov",
        },
        "japon_2011": {
            "evento": "Terremoto y tsunami de Tōhoku, Japón",
            "magnitud": "Mw 9.0 (2011)",
            "que_paso": (
                "Megasismo con tsunami devastador y un accidente nuclear en cascada en Fukushima."
            ),
            "lecciones": (
                "Los sistemas de alerta temprana y la evacuación por tsunami reducen víctimas; los "
                "efectos en cascada (energía, industria) deben preverse; la cultura de simulacros "
                "es un activo de resiliencia."
            ),
            "aplicacion_venezuela": (
                "Mapear riesgos en cascada sobre infraestructura crítica y promover simulacros "
                "comunitarios periódicos."
            ),
            "fuente": "https://www.jma.go.jp",
        },
        "mexico_2017": {
            "evento": "Terremoto de Puebla / Ciudad de México",
            "magnitud": "Mw 7.1 (2017)",
            "que_paso": (
                "Colapso de edificios —varios con planta baja débil— en zona urbana densa, con "
                "amplia movilización ciudadana en el rescate."
            ),
            "lecciones": (
                "La organización ciudadana en brigadas, bien coordinada, agiliza el rescate; la "
                "alerta sísmica (SASMEX) da segundos valiosos; conviene un censo de daños rápido y "
                "transparente."
            ),
            "aplicacion_venezuela": (
                "Canalizar el voluntariado en brigadas formadas y registradas, y montar un censo "
                "de daños ágil y verificable."
            ),
            "fuente": "http://www.ssn.unam.mx",
        },
        "ecuador_2016": {
            "evento": "Terremoto de Pedernales, Ecuador",
            "magnitud": "Mw 7.8 (2016)",
            "que_paso": (
                "Daños severos en la costa con miles de damnificados y necesidad de albergues y "
                "reconstrucción a gran escala."
            ),
            "lecciones": (
                "El financiamiento de la reconstrucción debe planificarse pronto; la coordinación "
                "de la ayuda internacional y la gestión ordenada de albergues son determinantes."
            ),
            "aplicacion_venezuela": (
                "Definir tempranamente esquemas de financiamiento y un modelo claro de gestión de "
                "albergues y ayuda externa."
            ),
            "fuente": "https://earthquake.usgs.gov",
        },
    },
    "indicadores": {
        "tasa_resolucion": {
            "definicion": "Porcentaje de reportes en estado 'Atendido' sobre el total del evento.",
            "como_calcularlo": "De por_status: conteo(Atendido) / total * 100.",
        },
        "tiempo_medio_atencion": {
            "definicion": "Tiempo promedio entre la creación del reporte y su cierre.",
            "como_calcularlo": "Diferencia entre createdAt y la fecha de cierre, si existe el campo.",
        },
        "cobertura_asignacion": {
            "definicion": "Porcentaje de reportes con responsable asignado.",
            "como_calcularlo": "De cobertura_asignacion: asignados / total * 100.",
            "no_usar": True,
            "motivo_no_usar": "El campo de asignación (assignedTo/Organismo) aún NO se "
                              "guarda de forma consistente en el origen; este indicador "
                              "genera ruido. NO lo reportes ni lo uses en los informes.",
        },
        "densidad_dano_por_estado": {
            "definicion": "Reportes de daño estructural por estado, idealmente normalizado por población.",
            "como_calcularlo": "De dano_estructural.por_estado dividido por la población del estado.",
        },
        "indice_desaparecidos_activos": {
            "definicion": "Desaparecidos aún no localizados sobre el total de reportes de desaparición.",
            "como_calcularlo": "desaparecidos no resueltos / desaparecidos totales * 100.",
        },
        "saturacion_geografica": {
            "definicion": "Concentración de reportes en clústeres geográficos (zonas críticas).",
            "como_calcularlo": "Análisis de densidad sobre puntos_geo validados (p. ej. por celdas).",
        },
        "velocidad_de_reporte": {
            "definicion": "Reportes por hora durante las primeras 72 horas del evento.",
            "como_calcularlo": "De evolucion_temporal con granularidad horaria en la ventana inicial.",
        },
        # ---- Indicadores propuestos (un comité avanzado podría adoptarlos) ----
        "indice_prioridad_rescate": {
            "definicion": "Score que combina daño estructural y posibles personas atrapadas por zona.",
            "como_calcularlo": "Ponderar reportes de colapso + desaparecidos por municipio para priorizar USAR.",
            "propuesto": True,
        },
        "brecha_asignacion_critica": {
            "definicion": "Reportes críticos (daño/desaparecidos) sin asignar respecto al total crítico.",
            "como_calcularlo": "criticos_sin_assignedTo / criticos_totales * 100.",
            "propuesto": True,
            "no_usar": True,
            "motivo_no_usar": "Depende del campo de asignación (assignedTo/Organismo), que "
                              "aún NO se guarda de forma consistente; genera ruido. NO lo uses.",
        },
        "tasa_reincidencia_zona": {
            "definicion": "Zonas que generan nuevos reportes tras una primera atención (réplicas/daño progresivo).",
            "como_calcularlo": "Reportes posteriores en el mismo municipio tras un cierre previo.",
            "propuesto": True,
        },
        "indice_estres_albergues": {
            "definicion": "Presión sobre la capacidad de albergue estimada por estado.",
            "como_calcularlo": "Damnificados estimados / capacidad declarada de albergues por estado.",
            "propuesto": True,
        },
        "cobertura_evidencia": {
            "definicion": "Proporción de reportes con evidencia adjunta (archivos) para verificación.",
            "como_calcularlo": "reportes con campo files no vacío / total * 100.",
            "propuesto": True,
        },
        "latencia_primer_contacto": {
            "definicion": "Tiempo hasta el primer cambio de estado desde 'Generado'.",
            "como_calcularlo": "Diferencia entre createdAt y el primer cambio de status registrado.",
            "propuesto": True,
        },
        "indice_punto_ciego": {
            "definicion": (
                "Mide cuánto se desvía una localidad de los reportes esperados según su exposición "
                "(MMI×población). Alto = muy expuesta y casi sin reportes → probable punto ciego."
            ),
            "como_calcularlo": (
                "tasa_global = Σ reportes_obs / Σ exposición (entre las que reportan); "
                "esperados = exposición × tasa_global; deficit = max(0, esperados − obs); "
                "indice = normalizar(deficit, 0-100) × peso_mmi (realce por cercanía a epicentro). "
                "Alerta CRÍTICA si MMI ≥ 6,0, habitantes ≥ 20.000 y cobertura < 0,25."
            ),
            "porque_importa": (
                "Lecciones de México 2017 y Turquía 2023: zonas que dejaron de reportar por colapso "
                "de comunicaciones resultaron de las más afectadas. El índice las eleva en prioridad."
            ),
            "propuesto": True,
        },
    },
    "contexto_evento": {
        "intensidad_mmi_24j": {
            "titulo": "Intensidad sísmica MMI por localidad — Terremoto 24J",
            "resumen": (
                "Referencia externa citable de sacudida (Modified Mercalli Intensity) y población "
                "por localidad para el 24J. Localidades de mayor MMI (eje epicentral Yaracuy–costa "
                "central): Puerto Cabello 8,0; Catia La Mar 7,9; Ocumare de la Costa 7,6; Maiquetía "
                "7,1; San Felipe 6,8; Caracas 6,8; La Guaira 6,6; Tucacas 6,6. Se usa para el cruce "
                "intensidad×reportes (puntos ciegos); las cifras de intensidad/población citan a la "
                "fuente, las de reportes salen de VenApp."
            ),
            "fuente_oficial": "El País (tabla ShakeMap/MMI 24J-2026) / USGS ShakeMap.",
        },
    },
}


def listar_temas() -> dict:
    """Claves disponibles por sección (para que el agente sepa qué puede pedir)."""
    return {k: list(v.keys()) for k, v in KNOWLEDGE.items()}


def consultar_conocimiento(seccion: str, clave: str | None = None) -> dict:
    """Si clave es None devuelve toda la sección; si no, la entrada puntual."""
    sec = KNOWLEDGE.get(seccion, {})
    if clave is None:
        return sec
    return {clave: sec.get(clave, {"error": "clave no encontrada"})}

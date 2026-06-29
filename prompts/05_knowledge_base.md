# Paso 05 — Base de conocimiento (protocolos internacionales + casos país)

## Objetivo
Crear `app/tools/knowledge_base.py`: conocimiento **curado y hardcoded** que casi no cambia, para
que el agente no dependa solo de la web. Es el "saber base" del comité de crisis: marcos de
referencia internacionales y lecciones de terremotos análogos. La web (Serper) se usa para
actualizar/ampliar; este módulo da el esqueleto sólido y citable.

## Reglas de redacción (importante)
- Escribir **resúmenes propios y parafraseados**, nunca copiar texto literal de manuales/sitios.
- Cada entrada incluye `fuente_oficial` (URL del organismo) para que el informe pueda citar.
- Tono institucional, conciso, accionable. Español.

## Estructura

### `app/tools/knowledge_base.py`
Define un diccionario `KNOWLEDGE` con tres secciones: `protocolos`, `casos_pais`, `indicadores`.
Y funciones de acceso. Esqueleto:

```python
KNOWLEDGE = {
  "protocolos": { ... },
  "casos_pais": { ... },
  "indicadores": { ... },
}

def listar_temas() -> dict:
    """Devuelve las claves disponibles por sección (para que el agente sepa qué puede pedir)."""
    return {k: list(v.keys()) for k, v in KNOWLEDGE.items()}

def consultar_conocimiento(seccion: str, clave: str | None = None) -> dict:
    """Si clave es None, devuelve toda la sección; si no, la entrada puntual."""
    sec = KNOWLEDGE.get(seccion, {})
    if clave is None:
        return sec
    return {clave: sec.get(clave, {"error": "clave no encontrada"})}
```

## Contenido a poblar (parafraseado, con URL de fuente)

### `protocolos`
- **`fema_ics`** — Sistema de Comando de Incidentes (ICS) y National Response Framework: estructura
  de mando unificado, funciones (operaciones, planificación, logística, finanzas), escalabilidad.
  Fuente: fema.gov.
- **`fema_damage_assessment`** — Evaluación preliminar de daños (PDA): niveles afectado/mayor/
  destruido, equipos de evaluación, priorización para asignación de recursos. Fuente: fema.gov.
- **`onu_insarag`** — Directrices INSARAG (ONU/OCHA) para búsqueda y rescate urbano (USAR):
  clasificación de equipos (ligero/mediano/pesado), marcado de estructuras, coordinación in situ
  (OSOCC), ventana crítica de las primeras 72–96 h. Fuente: insarag.org / unocha.org.
- **`onu_cluster`** — Sistema de clusters humanitarios (OCHA): salud, refugio, WASH, logística,
  protección, etc.; rol del coordinador humanitario. Fuente: humanitarianresponse.info.
- **`esfera`** — Manual Esfera (Sphere): estándares mínimos humanitarios en agua/saneamiento,
  alimentación, alojamiento y salud; carta humanitaria. Fuente: spherestandards.org.
- **`mira`** — Evaluación rápida inicial multisectorial (MIRA) para las primeras semanas.
- **`cruz_roja_rfl`** — Restablecimiento del contacto entre familiares (RFL) de la Cruz Roja/CICR:
  registro y búsqueda de personas desaparecidas, reunificación familiar. Fuente: icrc.org / familylinks.icrc.org.
- **`cruz_roja_aps`** — Apoyo psicosocial y primeros auxilios psicológicos (IFRC). Fuente: ifrc.org.
- **`proteccion_civil_ve`** — Marco de Protección Civil y Administración de Desastres de Venezuela:
  rol de organismos nacionales, regionales y municipales; coordinación de albergues y refugios.
  Fuente: portales oficiales venezolanos (citar con cautela; verificar vigencia con Serper).

### `casos_pais` (cada uno con: evento, magnitud, qué pasó, lecciones, aplicación a Venezuela, fuente)
- **`turquia_2023`** — Terremotos de Kahramanmaraş (Mw 7.8/7.5). Lecciones: importancia del código
  sísmico y su cumplimiento, colapso por construcción informal, logística de escombros, fatiga de
  coordinación, ventana de las 72 h. Fuente: USGS / informes ONU.
- **`chile_2010`** — Maule (Mw 8.8). Lecciones: códigos sísmicos estrictos salvaron vidas; fallas en
  alerta de tsunami; recuperación relativamente rápida; cultura de preparación. Fuente: USGS.
- **`japon_2011`** — Tōhoku (Mw 9.0). Lecciones: sistemas de alerta temprana, evacuación por
  tsunami, efecto cascada (nuclear), cultura de simulacros. Fuente: USGS / JMA.
- **`mexico_2017`** — Puebla/CDMX (Mw 7.1). Lecciones: rescate ciudadano organizado (brigadas),
  alerta sísmica SASMEX, colapso de edificios de planta baja débil, censo de daños. Fuente: USGS / SSN.
- **`ecuador_2016`** — Pedernales (Mw 7.8). Lecciones: financiamiento de reconstrucción, coordinación
  de ayuda internacional, gestión de albergues. Fuente: USGS / informes oficiales.

### `indicadores` (catálogo de indicadores que el comité podría adoptar)
Lista de indicadores con `definicion` y `como_calcularlo` (idealmente mapeable a la BD). Ej.:
- **`tasa_resolucion`** — % de reportes en estado `Atendido` sobre el total. (de `por_status`)
- **`tiempo_medio_atencion`** — diferencia entre `createdAt` y la fecha de cierre (si existe campo).
- **`cobertura_asignacion`** — % de reportes con responsable asignado. (de `cobertura_asignacion`)
- **`densidad_dano_por_estado`** — reportes de daño estructural por estado / población.
- **`indice_desaparecidos_activos`** — desaparecidos no localizados sobre total de desaparecidos.
- **`saturacion_geografica`** — clústeres geográficos de reportes (zonas de mayor concentración).
- **`velocidad_de_reporte`** — reportes por hora en las primeras 72 h (de `evolucion_temporal`).
Incluye 4–6 indicadores "nuevos/propuestos" que un comité avanzado podría inventar (el feature pide
"indicadores nuevos"), marcados como `propuesto: true`.

## Criterios de aceptación
- `consultar_conocimiento("protocolos", "onu_insarag")` devuelve un dict con `resumen` y `fuente_oficial`.
- `listar_temas()` devuelve las tres secciones con sus claves.
- Ninguna entrada copia texto literal de fuentes externas (todo parafraseado).

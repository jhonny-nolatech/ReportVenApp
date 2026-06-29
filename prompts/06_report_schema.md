# Paso 06 — Esquema del informe (Pydantic) y catálogo de tipos de reporte

## Objetivo
Definir el **contrato de datos del informe**. El agente NO escribirá Word directamente: producirá
un objeto JSON que cumple este esquema, y luego un renderer determinista lo convierte en `.docx`.
Esto garantiza informes consistentes y profesionales.

## Archivos a crear

### `app/agent/schema.py`
Define modelos Pydantic v2. Estructura del informe:

```python
from pydantic import BaseModel, Field
from typing import Literal

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
    evidencia_datos: str | None = None   # qué cifra de la BD lo respalda

class Prediccion(BaseModel):
    horizonte: str            # "24-72 h", "1-2 semanas", etc.
    prediccion: str
    supuestos: str | None = None

class CasoAnalogo(BaseModel):
    pais: str
    evento: str
    leccion: str
    aplicacion_venezuela: str
    fuente: str | None = None

class Protocolo(BaseModel):
    organismo: str            # FEMA, ONU/OCHA, Cruz Roja, Protección Civil...
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

class Fuente(BaseModel):
    titulo: str
    url: str | None = None

class PanoramaDatos(BaseModel):
    narrativa: str
    kpis: list[KPI] = []
    tablas: list[Tabla] = []

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
    panorama_datos: PanoramaDatos
    analisis_riesgos: list[Riesgo] = []
    predicciones: list[Prediccion] = []
    casos_analogos: list[CasoAnalogo] = []
    protocolos_recomendados: list[Protocolo] = []
    recomendaciones: list[Recomendacion] = []
    acciones_preventivas: list[AccionPreventiva] = []
    indicadores_nuevos: list[IndicadorNuevo] = []
    fuentes: list[Fuente] = []
    notas_pii: str = ("Este informe puede contener referencias agregadas a datos personales "
                      "autodeclarados. Uso oficial restringido; no difundir externamente.")
```

### Catálogo de tipos de reporte (en el mismo archivo)
```python
TIPOS_REPORTE = {
  "situacional_estrategico": {
     "label": "Situacional estratégico completo",
     "descripcion": "Panorama de datos + riesgos + predicciones + casos análogos + protocolos + recomendaciones + indicadores.",
     "secciones": "todas",
  },
  "resumen_ejecutivo": {
     "label": "Resumen ejecutivo rápido",
     "descripcion": "Versión corta: resumen, 5 KPIs, top riesgos y top recomendaciones.",
     "secciones": "reducidas",
  },
  "foco_desaparecidos": {
     "label": "Foco en personas desaparecidas",
     "descripcion": "Centrado en localización de personas: protocolos RFL/Cruz Roja, distribución geográfica, acciones.",
     "secciones": "desaparecidos",
  },
  "foco_dano_estructural": {
     "label": "Foco en daño estructural",
     "descripcion": "Edificaciones en riesgo, evaluación de daños, protocolos USAR/FEMA, priorización.",
     "secciones": "estructural",
  },
  "foco_geografico": {
     "label": "Foco geográfico (por estado)",
     "descripcion": "Análisis profundo de un estado/municipio específico.",
     "secciones": "geografico",
  },
}
```

Añade una función `validar_informe(data: dict) -> Informe` que parsee/valide el dict del agente y
lance error claro si no cumple el esquema.

## Criterios de aceptación
- `Informe.model_json_schema()` se genera sin error (lo usaremos para el tool del agente).
- `validar_informe(minimal_valid_dict)` retorna un `Informe`.
- `TIPOS_REPORTE` tiene al menos los 5 tipos descritos.

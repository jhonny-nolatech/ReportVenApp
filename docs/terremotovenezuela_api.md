# Fuente externa: API de TerremotoVenezuela.com

Evaluación de la API pública de **terremotovenezuela.com** (plataforma ciudadana
de mapeo de edificios afectados por el Terremoto 24J) como fuente complementaria
para los informes. Documentado tras exploración directa de la API.

## Resumen ejecutivo

- **Qué es:** plataforma ciudadana (NO oficial) que cura edificios afectados con
  foto, coordenadas y estado de verificación.
- **Veredicto:** **fuente complementaria, no reemplazo.** Su valor único son
  ~50 colapsos emblemáticos con **foto + coordenadas + verificación**. VenApp ya
  tiene órdenes de magnitud más reportes; la base de edificios debe salir de VenApp
  y TerremotoVenezuela sirve como **capa de evidencia visual / verificación**.
- **Limitación crítica:** la API devuelve **un máximo fijo de 50 registros** e
  **ignora `limit`/`skip`/`filter`**. No hay paginación funcional.

## Endpoints

Base: `https://api.terremotovenezuela.com/api/v1/`
Explorador / OpenAPI: `https://api.terremotovenezuela.com/explorer` ·
`https://api.terremotovenezuela.com/explorer/openapi.json` (stack LoopBack)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/edificios` | Lista de edificios afectados (**tope 50**) |
| GET | `/api/v1/edificios/{id}` | Detalle de un edificio |
| GET | `/api/v1/edificios/{id}/statuses` | Línea de tiempo de estatus (cambios de verificación/daño) |
| POST | `/api/v1/reportes` | Insertar un reporte (feed bidireccional) |

## Esquema de un edificio

```json
{
  "id": "uuid",
  "name": "Torre Petunia I y II",
  "address": "...", "city": "Caracas", "zone": "...",
  "lat": 10.50, "lng": -66.90,
  "damage_level": "total | severo | parcial",
  "status": "verificado | en_revision",
  "main_photo_url": "https://...supabase.co/.../damage-media/...",
  "media_urls": ["https://..."],
  "general_source": "Vecino | Familiar | Coberturas de medios | ...",
  "notes": "descripción del daño",
  "casualties_notes": null, "trapped_names": null, "has_missing_persons": false,
  "is_technically_evaluated": false,
  "created_at": "...", "last_updated_at": "..."
}
```

Las fotos se sirven desde Supabase Storage (bucket `damage-media`).

## Calidad de los datos (muestra de los 50 disponibles)

| Dimensión | Valor |
|---|---|
| Total recuperable | **50 (tope duro)** |
| Nivel de daño | 20 severo · 19 parcial · 11 total |
| Verificación | 18 verificado · 32 en revisión |
| Con coordenadas | 33/50 |
| Con foto | 36/50 |
| Evaluado por ingeniería (`is_technically_evaluated`) | 0/50 |
| Con atrapados nombrados | 6 |
| Fuente | mayormente "Vecino/Familiar" → ciudadana |
| Cobertura | ~40% Caracas + litoral (Catia La Mar, Caraballeda); resto disperso; incluye algún error (p. ej. ciudad "Vigo") |

## Comparación con VenApp

| | VenApp | TerremotoVenezuela API |
|---|---|---|
| Volumen evento 24J | ~8k–12k reportes (millones en `reports`) | **50 (tope)** |
| Origen | Ciudadano | Ciudadano (curado) |
| Foto | parcial | sí (36/50) |
| Estado de verificación | no | sí |
| Coordenadas | sí | parcial (33/50) |
| Cobertura nacional | amplia | Caracas-céntrica |

## Uso recomendado

1. **Enriquecimiento, no fuente primaria.** Cruzar sus ~50 edificios contra el
   inventario propio para adjuntar **foto + estado verificado + coordenadas** a
   colapsos emblemáticos.
2. **Feed recíproco.** Ellos exponen `POST /reportes` y solicitan fuentes externas;
   VenApp (con mucho más volumen) podría alimentarlos con agregados **sin PII**.

### Cruce realizado (referencia)

Contra el inventario consolidado del informe: de los 50, ~21 ya estaban presentes
y ~29 no. Tras descartar ruido (error "Vigo", casas genéricas), se integraron
**22 edificios verificados/con foto** (p. ej. Residencia Bellevue, Residencias
Bravamar, Residencias Atalaya, Hotel Catimar, Rompemar 1, Bloque 3 La Páez).

## Ejemplo de consulta

```bash
# Lista (recordar: devuelve como máximo 50, ignora filtros)
curl -s https://api.terremotovenezuela.com/api/v1/edificios

# Timeline de estatus de un edificio
curl -s https://api.terremotovenezuela.com/api/v1/edificios/{id}/statuses
```

> **Nota:** datos ciudadanos no oficiales — sirven para orientar inspección y
> aportar evidencia visual, no como confirmación técnica. Ningún registro está
> evaluado por ingeniería.

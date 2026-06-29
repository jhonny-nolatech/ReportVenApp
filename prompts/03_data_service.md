# Paso 03 — Capa de datos (agregaciones del evento + manejo de PII)

## Objetivo
Crear `app/db/data_service.py`: TODAS las consultas y agregaciones que un comité de crisis
necesita, devolviendo JSON limpio y serializable. Esta capa es la "fuente de verdad" cuantitativa
que luego consumirá el agente.

## Contexto: campos disponibles en `reports` (de la guía VenApp)
- Gestión: `number`, `numberSat`, `createdAt` (UTC), `status`, `sentManually`/"Enviado Manualmente".
- Clasificación: `category`, `subcategory.name`, `additionalcategory.name`,
  `extracategory.name` (tipo de emergencia: "Daño estructural grave", etc.).
- Geografía: `province.name` (estado), `municipality.name`, `parroquia.name`,
  `reportCommunity`, `location.coordinates` ([lng, lat] GeoJSON), `latitude`, `longitude`,
  `address`.
- Contenido: `title`, `description`.
- Asignación: `assignedTo` / "Asignado a".
- PII (autodeclarada, uso oficial restringido): `displayName`, `dni`, `phone_number`, `email`.
- Evidencias: `files`.

> Nota: en la imagen del Excel se ven columnas `ID, Codigo, UBCH, Enviado Manualmente, Asignado a,
> Fecha del incidente, Titulo`, pero la colección real tiene muchos más campos. Usa los de la guía.

## Requisitos de implementación

Todas las funciones reciben filtros opcionales `province`, `date_from`, `date_to` y construyen el
query con `build_event_query(...)` del paso 02. Devuelven dicts/listas JSON-serializables
(convertir `datetime` a ISO string, `ObjectId` a str). Zona horaria para agrupar por tiempo:
`America/Caracas` (UTC-4) usando `$dateToString` con `timezone`.

Implementa estas funciones en `app/db/data_service.py`:

1. `total_reportes(**f) -> int` — `count_documents(query)`.

2. `por_status(**f) -> list[dict]` — `$group` por `$status`, `$sort` desc. Incluye porcentaje.
   Marca `Atendido` como "resuelto".

3. `por_extracategoria(**f, top=20) -> list[dict]` — `$group` por `$extracategory.name`.

4. `por_subcategoria(**f, top=20) -> list[dict]`.

5. `por_estado_geografico(**f, top=30) -> list[dict]` — `$group` por `$province.name`.

6. `por_municipio(**f, top=30) -> list[dict]` — `$group` por `$municipality.name`
   (incluir `province.name` para contexto).

7. `evolucion_temporal(**f, granularidad="dia") -> list[dict]` — `$group` por fecha local
   (`$dateToString` con `timezone="America/Caracas"`, formato `%Y-%m-%d` para día u
   `%Y-%m-%d %H:00` para hora). Ordenado cronológicamente.

8. `cobertura_asignacion(**f) -> dict` — % de reportes con `assignedTo` no nulo vs sin asignar;
   también cuántos `sentManually == true`.

9. `desaparecidos(**f, limit=15) -> dict` — detectar reportes de personas desaparecidas combinando
   `extracategory.name`/`subcategory.name` y keywords en `title`/`description`
   (regex insensible a mayúsculas: `desaparec|no aparece|no localiza|paradero`). Devolver:
   `{"conteo": int, "por_estado": [...], "muestra": [reportes redactados]}`.

10. `dano_estructural(**f, limit=15) -> dict` — similar con keywords
    `estructural|colaps|derrumb|grieta|agriet|fisura|fractur|punto de caer|riesgo de colapso`.
    Devolver conteo, desglose por estado y muestra redactada.

11. `puntos_geo(**f, limit=2000) -> list[dict]` — extraer `location.coordinates` (o
    `latitude`/`longitude`), **validar** que caen dentro de `VEN_BBOX` (descarta mal
    geolocalizados), devolver `[{"lat":..., "lng":..., "extracategoria":..., "estado":...}]`.

12. `muestra_reportes(focus=None, limit=20, include_pii=False, **f) -> list[dict]` — devuelve
    reportes con la proyección útil. `focus` puede ser `"desaparecidos"`, `"dano_estructural"`,
    `"general"`. Aplica el filtro de keywords correspondiente.

13. `panorama_completo(**f) -> dict` — orquesta todas las anteriores y devuelve un único dict
    con todo (total, por_status, por_extracategoria, por_estado_geografico, evolucion_temporal,
    cobertura_asignacion, desaparecidos, dano_estructural, puntos_geo resumidos). Este será el
    payload principal que consuma el agente.

14. `listar_estados(**f) -> list[str]` — `distinct("province.name", query)` para poblar el dropdown
    del frontend.

## Manejo de PII (obligatorio)
- Implementa `redactar(doc: dict) -> dict` que reemplace `displayName`, `dni`, `phone_number`,
  `email` por `"[REDACTADO]"` y recorte `address` a solo municipio/parroquia si es posible.
- **`include_pii=False` por defecto en todo.** Solo si quien llama lo activa explícitamente se
  devuelve PII (uso oficial). Documenta esta regla con un comentario visible.

## Criterios de aceptación
- `python -c "from app.db.data_service import panorama_completo; import json; print(json.dumps(panorama_completo(), ensure_ascii=False)[:500])"` imprime JSON válido.
- `desaparecidos()["muestra"]` nunca contiene PII si `include_pii=False`.
- Ningún resultado incluye `datetime`/`ObjectId` crudos (todo serializable).

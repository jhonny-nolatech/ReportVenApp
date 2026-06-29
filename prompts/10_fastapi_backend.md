# Paso 10 — Backend FastAPI (API + descarga + healthcheck)

## Objetivo
Crear `app/api/main.py`: una API que orqueste todo y sirva el frontend. Punto de entrada del
sistema.

## Endpoints

### `GET /api/health`
Devuelve `{"ok": true, "db": <ping>, "evento": "Terremoto 24J"}`. Hace ping a Mongo; si falla,
`ok: false` con el error (sin filtrar credenciales).

### `GET /api/tipos-reporte`
Devuelve `TIPOS_REPORTE` (del paso 06) + la lista de estados disponibles
(`data_service.listar_estados()`) para poblar el frontend:
```json
{"tipos": {...}, "estados": ["Distrito Capital", "Miranda", ...]}
```
Cachear `estados` unos minutos para no golpear la BD en cada carga.

### `POST /api/reportes`
Body:
```json
{
  "tipo": "situacional_estrategico",
  "estado": "Distrito Capital",          // opcional
  "instruccion_adicional": "...",         // opcional
  "modelo": "claude-sonnet-4-6"           // opcional
}
```
Flujo:
1. Llama `orchestrator.generar_informe_dict(tipo, estado, instruccion_adicional, modelo)`.
2. Renderiza con `docx_renderer.render_informe(informe, out_path)`.
3. Devuelve:
```json
{
  "report_id": "informe_situacional_estrategico_20260626_1530",
  "resumen_ejecutivo": "...",
  "kpis": [...],
  "n_recomendaciones": 7,
  "n_riesgos": 4,
  "download_url": "/api/reportes/{report_id}/docx"
}
```
- La generación puede tardar (decenas de segundos). Usar `async def` y ejecutar el trabajo
  pesado en un threadpool (`await run_in_threadpool(...)` de Starlette) para no bloquear el loop.
- Timeout generoso y manejo de errores con `HTTPException` (mensajes claros, sin credenciales).
- Guardar el informe JSON también (`reports_out/{report_id}.json`) por trazabilidad.

### `GET /api/reportes/{report_id}/docx`
Devuelve el `.docx` con `FileResponse` y
`media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"` y
`Content-Disposition: attachment; filename=...`. Validar que `report_id` no tenga path traversal
(solo `[A-Za-z0-9_]+`).

### Servir el frontend
- Montar `app/api/static` como estáticos y servir `index.html` en `GET /`.
  ```python
  from fastapi.staticfiles import StaticFiles
  app.mount("/static", StaticFiles(directory="app/api/static"), name="static")
  ```
  y un handler para `/` que devuelva el `index.html`.

## Requisitos
- CORS abierto solo a localhost en desarrollo (configurable).
- No imprimir ni devolver nunca la cadena de conexión, claves ni PII.
- Estructura limpia: la API solo orquesta; la lógica vive en las capas previas.

## Criterios de aceptación
- `uvicorn app.api.main:app --reload` levanta sin error.
- `GET /api/health` responde `ok: true`.
- `POST /api/reportes` con `{"tipo":"resumen_ejecutivo"}` devuelve un `download_url` y el archivo se
  puede descargar y abrir.

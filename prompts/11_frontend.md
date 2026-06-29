# Paso 11 — Interfaz web sencilla

## Objetivo
Crear `app/api/static/index.html`: una página única, limpia y sin tooling, para que cualquier
persona del equipo genere informes en dos clics. Servida por FastAPI (paso 10). Sin build, sin
Node: HTML + Tailwind por CDN + JS vanilla con `fetch`.

## Requisitos de UX
- Cabecera con título "Copiloto Estratégico — Terremoto 24J" y la etiqueta de clasificación.
- Formulario:
  1. **Tipo de informe**: `<select>` poblado desde `GET /api/tipos-reporte` (muestra `label`,
     valor = clave; muestra la `descripcion` del tipo seleccionado debajo).
  2. **Estado/provincia**: `<select>` poblado con `estados` (opción "Nacional" = sin filtro).
     Se habilita/resalta sobre todo para el tipo `foco_geografico`.
  3. **Instrucción adicional**: `<textarea>` libre ("Enfócate en Caracas y compara con México 2017",
     etc.).
  4. **Modelo** (opcional, avanzado): selector `claude-sonnet-4-6` (rápido) / `claude-opus-4-8`
     (más exhaustivo). Por defecto Sonnet.
  5. Botón **"Generar informe"**.
- Al enviar:
  - Deshabilitar el botón y mostrar un estado de carga con mensajes rotando ("Consultando base de
    datos…", "Analizando riesgos…", "Buscando casos análogos…", "Redactando informe…"). Como el
    backend es síncrono, basta con un spinner + texto; el tiempo puede ser ~20–60 s.
  - Al recibir respuesta: mostrar tarjeta con **resumen ejecutivo**, los **KPIs** (chips/tarjetas),
    nº de riesgos y recomendaciones, y un botón grande **"Descargar Word"** que apunte a
    `download_url`.
  - Manejo de errores visible (mensaje claro si la API falla).
- Diseño: tarjetas, buena tipografía, paleta sobria coherente con el Word (azul/teal `#0B3C5D`),
  responsive. Nada recargado.
- Historial ligero (opcional): lista en memoria de los informes generados en la sesión con sus
  enlaces de descarga. (No usar localStorage si no hace falta; mantener en variable JS.)

## Notas técnicas
- Todo en un solo `index.html` (CSS en `<style>` o Tailwind CDN, JS en `<script>`).
- Usar `fetch('/api/...')` (mismo origen, sin CORS).
- No exponer claves ni PII en el frontend (no hay; la API ya las protege).

## Criterios de aceptación
- Abrir `http://localhost:8000/` muestra el formulario con tipos y estados cargados desde la API.
- Generar un "Resumen ejecutivo rápido" muestra el resumen + KPIs y permite descargar el `.docx`.
- La página funciona en escritorio y móvil sin romperse.

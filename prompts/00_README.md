# Copiloto Estratégico de Crisis — Terremoto 24J (VenApp / Línea 58)

Secuencia de prompts para **Claude Code**. Construyen, paso a paso, un sistema multiagente
que se conecta a la base de datos de reportes ciudadanos del sismo, consulta protocolos
internacionales (FEMA, ONU/OCHA, Cruz Roja, etc.), busca casos análogos y **genera informes
estratégicos en Word** bajo demanda, desde una interfaz web sencilla.

## Qué se construye

```
copiloto-crisis-24j/
├── app/
│   ├── config.py            # carga de .env y constantes del evento
│   ├── db/
│   │   ├── mongo.py         # conexión read-only TLS al replica set
│   │   └── data_service.py  # todas las agregaciones/consultas del evento
│   ├── tools/
│   │   ├── serper.py        # búsqueda web (Serper)
│   │   └── knowledge_base.py# conocimiento hardcoded (protocolos + casos país)
│   ├── agent/
│   │   ├── schema.py        # esquema Pydantic del informe + tipos de reporte
│   │   ├── tools_def.py     # definición de tools Anthropic + dispatcher
│   │   └── orchestrator.py  # loop agéntico (el "copiloto estratégico")
│   ├── report/
│   │   └── docx_renderer.py # JSON del informe -> Word profesional
│   └── api/
│       ├── main.py          # FastAPI (endpoints + sirve el frontend)
│       └── static/index.html# interfaz web sencilla
├── scripts/
│   ├── smoke_db.py          # prueba de conexión y conteo del evento
│   └── run.sh               # arranque
├── reports_out/             # .docx generados (ignorado por git)
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Orden de ejecución (un prompt por paso)

| Paso | Archivo | Construye |
|------|---------|-----------|
| 01 | `01_scaffold.md` | Estructura, dependencias, config, .env.example, .gitignore |
| 02 | `02_mongo_connector.md` | Conexión Mongo read-only (TLS mutuo, secundario, guardas) |
| 03 | `03_data_service.md` | Capa de datos: todas las agregaciones del evento + manejo PII |
| 04 | `04_serper_tool.md` | Herramienta de búsqueda web (Serper) |
| 05 | `05_knowledge_base.md` | Base de conocimiento (protocolos internacionales + casos país) |
| 06 | `06_report_schema.md` | Esquema del informe (Pydantic) y catálogo de tipos de reporte |
| 07 | `07_agent_tools.md` | Definición de tools para Claude + dispatcher |
| 08 | `08_agent_orchestrator.md` | Loop agéntico que produce el informe estructurado |
| 09 | `09_docx_renderer.md` | Render del informe a Word profesional |
| 10 | `10_fastapi_backend.md` | API FastAPI + descarga + healthcheck |
| 11 | `11_frontend.md` | Interfaz web sencilla |
| 12 | `12_integration_run.md` | Integración, scripts, pruebas y checklist de seguridad |

## Cómo usar estos prompts

1. Abre Claude Code en una carpeta vacía nueva (ej. `copiloto-crisis-24j/`).
2. Copia el contenido del prompt del paso correspondiente y pégalo como instrucción.
3. Deja que Claude Code cree/edite los archivos. Revisa el diff antes de aceptar.
4. Pasa al siguiente paso solo cuando se cumplan los **Criterios de aceptación**.

## Requisitos previos (los tienes tú, no van en git)

- `.env` real (a partir de `.env.example`) con `ANTHROPIC_API_KEY`, `SERPER_API_KEY`, `PRODdbURL`.
- Certificados TLS en `mongo_ssl_vevaprd_rs03_app/`: `CA.pem` y `mclient.pem`.
- Python 3.10+.

## Seguridad (importante)

- **Solo lectura** sobre producción. Nunca insertar/actualizar/borrar.
- **Siempre** filtrar por `category == "Terremoto 24J"` **y** `createdAt >= 2026-06-24` (UTC).
- Leer del **secundario** (`SECONDARY_PREFERRED`).
- PII (`displayName`, `dni`, `phone_number`, `email`, `address`): **redactada por defecto**.
- Si pegaste credenciales en algún lugar inseguro, **rótalas**.

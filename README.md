# Copiloto Estratégico de Crisis — Terremoto 24J (VenApp / Línea 58)

Sistema multiagente que se conecta (**solo lectura**) a la base de reportes
ciudadanos del sismo del **24-jun-2026** en Venezuela, consulta protocolos
internacionales (FEMA, ONU/OCHA/INSARAG, Esfera, Cruz Roja), busca casos análogos
y **genera informes estratégicos en Word** bajo demanda, desde una interfaz web
sencilla.

Cada informe incluye: panorama de datos, análisis de riesgos, predicciones, casos
análogos internacionales, protocolos recomendados, recomendaciones priorizadas
(P1/P2/P3), acciones preventivas e indicadores nuevos propuestos.

## Arquitectura

```
app/
├── config.py            # carga de .env + constantes del evento
├── db/mongo.py          # conexión read-only TLS al replica set (proxy anti-escritura)
├── db/data_service.py   # agregaciones del evento + manejo de PII
├── tools/serper.py      # búsqueda web (Serper)
├── tools/knowledge_base.py  # protocolos + casos país (curado)
├── agent/schema.py      # esquema Pydantic del informe + tipos de reporte
├── agent/tools_def.py   # tools de Anthropic + dispatcher
├── agent/orchestrator.py# loop agéntico (el "copiloto")
├── report/docx_renderer.py  # JSON -> Word profesional
└── api/main.py + static/index.html  # FastAPI + frontend
```

## Requisitos

- Python 3.10+
- `.env` (a partir de `.env.example`) con `ANTHROPIC_API_KEY`, `SERPER_API_KEY`, `PRODdbURL`.
- Certificados TLS en `mongo_ssl_vevaprd_rs03_app/`: `CA.pem` y `mclient.pem`.

## Cómo correr

```bash
cp .env.example .env      # rellena las claves reales
bash scripts/run.sh       # crea venv, instala deps y levanta http://localhost:8000
```

Abre `http://localhost:8000`, elige tipo de informe y estado, y genera. La
generación tarda ~20–60 s (consume tokens de Anthropic).

### Suite de informes (un solo comando)

Genera el informe base **y** los tres derivados encadenados, con densidad
poblacional, datos de TerremotoVenezuela y gráficos embebidos en el técnico:

```bash
source .venv/bin/activate
python scripts/generar_suite.py                  # nacional
python scripts/generar_suite.py -e "La Guaira"   # con foco geográfico
```

Salida en `reports_out/`: `INFORME_BASE.docx`, `INFORME_TECNICO_OPERATIVO.docx`
(con pizzas de infraestructura), `BRIEF_PRESIDENCIAL.docx` y
`PLAN_DE_COMUNICACION_DE_EMERGENCIA.docx`. Los prompts viven en
`prompts/informes/` y las áreas para densidad en `data_seed/areas_municipios.csv`.

## Pruebas (en orden)

```bash
source .venv/bin/activate
python scripts/smoke_db.py     # ping ok + conteo del evento > 0
python -c "from app.db.data_service import panorama_completo; print(len(str(panorama_completo())))"
python -c "from app.tools.serper import buscar_web; print(buscar_web('INSARAG USAR', num=2)['resultados'][0]['url'])"
python -c "from app.tools.knowledge_base import listar_temas; print(listar_temas())"
python scripts/test_e2e.py     # genera reports_out/test_e2e.docx
bash scripts/run.sh            # flujo completo desde el navegador
```

## Extender el sistema

- **Nuevo tipo de informe:** añade una entrada a `TIPOS_REPORTE` en
  [app/agent/schema.py](app/agent/schema.py).
- **Ampliar conocimiento:** edita el diccionario `KNOWLEDGE` en
  [app/tools/knowledge_base.py](app/tools/knowledge_base.py) (parafrasea, con fuente).

## Costos

Cada informe consume tokens de Anthropic. Sonnet 4.6 es más barato y rápido;
Opus 4.8 es más exhaustivo (y más caro). El selector de modelo está en el frontend.

## Checklist de seguridad

- [x] `.env` y `*.pem` en `.gitignore`, no versionados.
- [x] Toda consulta a `reports` pasa por `build_event_query()` (categoría + fecha).
- [x] Conexión `SECONDARY_PREFERRED`; colección **solo lectura** (proxy bloquea escrituras).
- [x] PII redactada por defecto (`include_pii=False`) en muestras; nunca expuesta individualmente.
- [x] La API no devuelve la cadena de conexión, claves ni PII en errores (`_safe_err`).
- [x] `report_id` validado contra path traversal (`^[A-Za-z0-9_]+$`).
- [ ] **Rotar** cualquier credencial que se haya compartido en texto plano.

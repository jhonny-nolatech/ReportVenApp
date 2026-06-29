# Paso 12 — Integración, arranque, pruebas y checklist de seguridad

## Objetivo
Atar todo: scripts de arranque, prueba end-to-end, documentación de uso y verificación final de
seguridad.

## Archivos a crear / completar

### `scripts/run.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv 2>/dev/null || true
source .venv/bin/activate
pip install -q -r requirements.txt
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```
(Equivalente `run.ps1` para Windows si aplica.)

### `scripts/test_e2e.py`
Prueba end-to-end sin frontend:
```python
from app.agent.orchestrator import generar_informe_dict
from app.report.docx_renderer import render_informe
import json, os
inf = generar_informe_dict("resumen_ejecutivo", modelo="claude-sonnet-4-6")
print("Resumen:", inf["resumen_ejecutivo"][:200])
print("Recomendaciones:", len(inf.get("recomendaciones", [])))
path = render_informe(inf, "reports_out/test_e2e.docx")
print("DOCX:", path, "existe:", os.path.exists(path))
```

### `README.md` del proyecto (completar)
Debe incluir:
- Qué es y qué genera.
- Requisitos: Python 3.10+, `.env` (a partir de `.env.example`), certificados TLS en
  `mongo_ssl_vevaprd_rs03_app/`.
- Pasos: `cp .env.example .env` → rellenar → `bash scripts/run.sh` → abrir `http://localhost:8000`.
- Cómo añadir un nuevo tipo de informe (editar `TIPOS_REPORTE`).
- Cómo ampliar la base de conocimiento (editar `knowledge_base.py`).
- Nota de costos: cada informe consume tokens de Anthropic (Sonnet barato, Opus más caro).

## Pruebas a ejecutar (en orden)
1. `python scripts/smoke_db.py` → ping `ok` y conteo del evento > 0.
2. `python -c "from app.db.data_service import panorama_completo; print(len(str(panorama_completo())))"`.
3. `python -c "from app.tools.serper import buscar_web; print(buscar_web('INSARAG USAR', num=2)['resultados'][0]['url'])"`.
4. `python -c "from app.tools.knowledge_base import listar_temas; print(listar_temas())"`.
5. `python scripts/test_e2e.py` → genera `reports_out/test_e2e.docx`.
6. `bash scripts/run.sh` y probar el flujo completo desde el navegador.

## Checklist de seguridad (verificar y dejar documentado)
- [ ] `.env` y `*.pem` están en `.gitignore` y NO versionados.
- [ ] Toda consulta a `reports` pasa por `build_event_query()` (categoría + fecha).
- [ ] La conexión usa `SECONDARY_PREFERRED` y la colección es de **solo lectura** (proxy bloquea
      escrituras).
- [ ] PII redactada por defecto en muestras y nunca expuesta individualmente en informes ni API.
- [ ] La API no devuelve la cadena de conexión, claves ni PII en errores.
- [ ] `report_id` validado contra path traversal en la descarga.
- [ ] Las credenciales que se hayan compartido en texto plano fueron **rotadas**.

## Criterios de aceptación final
- El flujo completo funciona: navegador → seleccionar tipo → generar → descargar Word con un informe
  fundamentado en datos reales del evento, con riesgos, predicciones, casos análogos, protocolos,
  recomendaciones e indicadores.
- El sistema no escribe en producción ni expone PII.

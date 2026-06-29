# Paso 01 — Scaffold del proyecto

## Objetivo
Crear la estructura base del proyecto `copiloto-crisis-24j`, las dependencias, la configuración
central y la higiene de secretos. Nada de lógica de negocio todavía.

## Contexto
Vamos a construir un copiloto estratégico de crisis para el "Terremoto 24J" (Venezuela,
24-jun-2026). El sistema se conectará a MongoDB de producción (solo lectura), buscará en web
(Serper), tendrá conocimiento de protocolos internacionales y generará informes en Word vía un
agente de Anthropic. Este paso solo prepara el terreno.

## Archivos a crear

### `requirements.txt`
```
anthropic>=0.40.0
pymongo>=4.8.0
python-dotenv>=1.0.1
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
python-docx>=1.1.2
requests>=2.32.0
pydantic>=2.8.0
```

### `.gitignore`
Debe ignorar como mínimo: `.env`, `*.pem`, `mongo_ssl_*/`, `__pycache__/`, `.venv/`, `venv/`,
`reports_out/`, `*.docx`, `.DS_Store`.

### `.env.example`  (SOLO placeholders, nunca valores reales)
```dotenv
# Anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
ANTHROPIC_MODEL=claude-sonnet-4-6
ANTHROPIC_MODEL_SYNTHESIS=claude-opus-4-8

# Serper (búsqueda web)
SERPER_API_KEY=xxxxxxxx

# MongoDB producción VenApp (replica set, TLS mutuo)
PRODdbURL=mongodb://USUARIO:CLAVE@HOST1,HOST2,HOST3/venapp_db?replicaSet=NOMBRE_RS&ssl=true
REPLICA_SET=vevaprd-rs03
mongoSslCAFile=mongo_ssl_vevaprd_rs03_app/CA.pem
mongoSslPEMKeyFile=mongo_ssl_vevaprd_rs03_app/mclient.pem

# App
REPORTS_OUT_DIR=reports_out
APP_TIMEZONE=America/Caracas
```

### `app/config.py`
Módulo de configuración central. Requisitos:
- Cargar `.env` con `python-dotenv` (`load_dotenv()`).
- Exponer una clase/objeto `Settings` (puede ser un dataclass o pydantic-settings) con:
  `anthropic_api_key`, `anthropic_model`, `anthropic_model_synthesis`, `serper_api_key`,
  `prod_db_url`, `mongo_ca_file`, `mongo_pem_file`, `reports_out_dir`, `app_timezone`.
- Constantes del evento (no van en .env porque no cambian):
  ```python
  import datetime as dt
  EVENT_CATEGORY = "Terremoto 24J"
  EVENT_START = dt.datetime(2026, 6, 24, 0, 0, 0)  # UTC, naive
  EVENT_NAME = "Terremoto 24J — Venezuela"
  # Bounding box aproximado de Venezuela para validar coordenadas (lat, lng)
  VEN_BBOX = {"lat_min": 0.6, "lat_max": 12.3, "lng_min": -73.4, "lng_max": -59.7}
  # Estados de gestión posibles del campo `status`
  STATUS_VALUES = ["Generado","Recibido","Asignado","En Proceso","Atendido","Devuelto","Rechazado"]
  ```
- Una función `validate()` que falle con mensaje claro si falta `ANTHROPIC_API_KEY`,
  `PRODdbURL` o los certificados no existen en disco (usar `os.path.exists`).
- Crear `reports_out_dir` si no existe.

### `README.md` (del proyecto, breve)
Resumen del propósito + cómo correr (lo completaremos en el paso 12).

## Criterios de aceptación
- `python -c "from app.config import Settings; s=Settings(); print(s.anthropic_model)"` no falla
  (con un `.env` presente).
- `.env` y `*.pem` están en `.gitignore`.
- No hay ningún secreto real en archivos versionados.

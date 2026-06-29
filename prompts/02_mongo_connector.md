# Paso 02 — Conector MongoDB (solo lectura, TLS mutuo)

## Objetivo
Crear el módulo de conexión a la base de datos de producción de VenApp con todas las guardas de
seguridad. Conexión **solo lectura**, **secundario preferido**, autenticación **TLS mutua**.

## Contexto / reglas de oro (de la guía oficial VenApp)
- Colección de interés: `reports` en la base `venapp_db` (viene en la URI).
- Solo nos importan los reportes del evento: `category == "Terremoto 24J"`.
- SIEMPRE acotar por fecha: `createdAt >= 2026-06-24` (UTC). La colección tiene millones de docs.
- Leer del **secundario** (`SECONDARY_PREFERRED`) para no cargar el primario.
- **Nunca** `find()` sin filtro de fecha. **Nunca** escribir en producción.

## Archivos a crear

### `app/db/mongo.py`
Requisitos:

```python
import os
from functools import lru_cache
from pymongo import MongoClient, ReadPreference
from app.config import Settings

@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    s = Settings()
    client = MongoClient(
        s.prod_db_url,
        tls=True,
        tlsCAFile=s.mongo_ca_file,
        tlsCertificateKeyFile=s.mongo_pem_file,
        serverSelectionTimeoutMS=15000,
        read_preference=ReadPreference.SECONDARY_PREFERRED,
        appname="copiloto-crisis-24j",
    )
    return client

def get_reports_collection():
    client = get_client()
    db = client.get_default_database()   # venapp_db (de la URI)
    return db["reports"]

def ping() -> dict:
    return get_client().admin.command("ping")
```

Añadir además:
- Una **guarda anti-escritura**: una función `assert_read_only()` o un wrapper que documente y, si
  es práctico, envuelva la colección de forma que `insert*/update*/delete*/replace*/drop` lancen
  `RuntimeError("Operación de escritura bloqueada: producción es solo lectura")`. Implementarlo con
  una clase proxy ligera `ReadOnlyCollection` que delega solo en métodos de lectura permitidos
  (`find`, `find_one`, `count_documents`, `aggregate`, `distinct`, `estimated_document_count`).
  `get_reports_collection()` debe devolver esta colección proxy.
- Función `build_event_query(province: str | None = None, date_from=None, date_to=None) -> dict`
  que construya SIEMPRE el filtro base del evento:
  ```python
  from app.config import EVENT_CATEGORY, EVENT_START
  q = {"category": EVENT_CATEGORY, "createdAt": {"$gte": date_from or EVENT_START}}
  if date_to: q["createdAt"]["$lte"] = date_to
  if province: q["province.name"] = province
  return q
  ```
  Esta función es la **única** forma autorizada de construir queries sobre `reports`. Documentarlo.

### `scripts/smoke_db.py`
Script de humo:
```python
from app.db.mongo import ping, get_reports_collection, build_event_query
print("ping:", ping())
col = get_reports_collection()
print("Reportes Terremoto 24J:", col.count_documents(build_event_query()))
```

## Criterios de aceptación
- `python scripts/smoke_db.py` imprime `{'ok': 1.0}` y un conteo entero > 0.
- Intentar `get_reports_collection().insert_one({})` lanza `RuntimeError`.
- No existe ninguna ruta de código que haga `find`/`aggregate` sobre `reports` sin pasar por
  `build_event_query()`.
